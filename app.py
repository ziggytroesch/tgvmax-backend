from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
API_URL = "https://data.sncf.com/api/records/1.0/search/"

@app.route("/tgvmax", methods=["GET"])
def get_tgvmax_routes():
    from_station = request.args.get("from")
    to_station = request.args.get("to")
    date = request.args.get("date")

    if not from_station or not to_station or not date:
        return jsonify({"error": "Missing parameters"}), 400

    params = {
        "dataset": "tgvmax",
        "rows": 1000,
        "refine.date": date
    }

    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        trains = [r["fields"] for r in data.get("records", [])]

        def time_diff_minutes(t1, t2):
            h1, m1 = map(int, t1.split(":"))
            h2, m2 = map(int, t2.split(":"))
            return (h2 * 60 + m2) - (h1 * 60 + m1)

        def find_itineraries(from_, to_, trains):
            itineraries = []
            for t1 in trains:
                if t1["origine"] != from_:
                    continue
                arr1 = t1["arrival_time"]
                for t2 in trains:
                    if t2["origine"] != t1["destination"]:
                        continue
                    wait = time_diff_minutes(arr1, t2["departure_time"])
                    if wait < 15 or wait > 120:
                        continue
                    if t2["destination"] == to_:
                        itineraries.append([t1, t2])
                    else:
                        for t3 in trains:
                            if t3["origine"] != t2["destination"] or t3["destination"] != to_:
                                continue
                            wait2 = time_diff_minutes(t2["arrival_time"], t3["departure_time"])
                            if 15 <= wait2 <= 120:
                                itineraries.append([t1, t2, t3])
            return itineraries

        direct = [t for t in trains if t.get("origine") == from_station and t.get("destination") == to_station]
        itineraries = find_itineraries(from_station, to_station, trains)

        return jsonify({"direct": direct, "itineraries": itineraries})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
