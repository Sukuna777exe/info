from flask import jsonify, request, Blueprint, Response
import requests
import binascii
from datetime import datetime
import json
import os
from pymongo import MongoClient
from app.core.encrypt import Encrypt_ID, encrypt_api
from app.core.parser import get_available_room

routes = Blueprint("routes", __name__)

# MongoDB connection setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.info  # database name
tokens_collection = db.tokens  # tokens collection

def safe_get(data, *keys, default="N/A"):
    try:
        for key in keys:
            data = data[key]
        return data
    except Exception:
        return default

def get_jwt_tokens():
    tokens_cursor = tokens_collection.find({})
    tokens = {}
    for doc in tokens_cursor:
        region = doc.get("region")
        token = doc.get("token")
        if region and token:
            tokens[region] = token
    return tokens

def get_url(region):
    if region == "ind":
        return "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
    elif region in {"br", "us", "sac", "na"}:
        return "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
    else:
        return "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"

def build_headers(token):
    return {
        "X-Unity-Version": "2018.4.11f1",
        "ReleaseVersion": "OB48",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-GA": "v1 1",
        "Authorization": f"Bearer {token}",
        "Content-Length": "16",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2; ASUS_Z01QD Build/QKQ1.190825.002)",
        "Host": "clientbp.ggblueshark.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
    }

def parse_response(response_content, player_id):
    hex_response = binascii.hexlify(response_content).decode("utf-8")
    json_result = get_available_room(hex_response)
    parsed_data = json.loads(json_result)
    player_info = {
        "nikname": safe_get(parsed_data, "1", "data", "3", "data"),
        "uid": player_id,
        "likes": safe_get(parsed_data, "1", "data", "21", "data"),
        "level": safe_get(parsed_data, "1", "data", "6", "data"),
        "signature": safe_get(parsed_data, "9", "data", "9", "data"),
        "release_version": safe_get(parsed_data, "1", "data", "50", "data"),
        "bp_level": safe_get(parsed_data, "1", "data", "18", "data"),
        "cs_rank_points": safe_get(parsed_data, "1", "data", "31", "data"),
        "br_rank_points": safe_get(parsed_data, "1", "data", "15", "data"),
        "banner_id": safe_get(parsed_data, "1", "data", "11", "data"),
        "avatar_id": safe_get(parsed_data, "1", "data", "12", "data"),
        "title_id": safe_get(parsed_data, "1", "data", "48", "data"),
        "exp": safe_get(parsed_data, "1", "data", "7", "data"),
        "region": safe_get(parsed_data, "1", "data", "5", "data"),
        "honor_score": safe_get(parsed_data, "11", "data", "1", "data"),
        "account_created": datetime.fromtimestamp(
            safe_get(parsed_data, "1", "data", "44", "data", default=0)
        ).strftime("%Y-%m-%d %I:%M:%S %p") if safe_get(parsed_data, "1", "data", "44", "data", default=0) else "N/A",
        "last_login": datetime.fromtimestamp(
            safe_get(parsed_data, "1", "data", "24", "data", default=0)
        ).strftime("%Y-%m-%d %I:%M:%S %p") if safe_get(parsed_data, "1", "data", "24", "data", default=0) else "N/A",
    }

    pet_info = None
    if "8" in parsed_data:
        pet_info = {
            "id": safe_get(parsed_data, "8", "data", "1", "data"),
            "name": safe_get(parsed_data, "8", "data", "2", "data"),
            "level": safe_get(parsed_data, "8", "data", "3", "data"),
            "exp": safe_get(parsed_data, "8", "data", "4", "data"),
            "is_selected": safe_get(parsed_data, "8", "data", "5", "data"),
            "skin_id": safe_get(parsed_data, "8", "data", "6", "data"),
            "selected_skill_id": safe_get(parsed_data, "8", "data", "9", "data")
        }

    guild_info = None
    if "6" in parsed_data and "7" in parsed_data:
        guild_info = {
            "guild_id": safe_get(parsed_data, "6", "data", "1", "data"),
            "name": safe_get(parsed_data, "6", "data", "2", "data"),
            "owner": safe_get(parsed_data, "6", "data", "3", "data"),
            "level": safe_get(parsed_data, "6", "data", "4", "data"),
            "capacity": safe_get(parsed_data, "6", "data", "5", "data"),
            "members": safe_get(parsed_data, "6", "data", "6", "data"),
            "owner_basic_info": {
                "uid": safe_get(parsed_data, "7", "data", "1", "data"),
                "nickname": safe_get(parsed_data, "7", "data", "3", "data"),
                "level": safe_get(parsed_data, "7", "data", "6", "data"),
                "likes": safe_get(parsed_data, "7", "data", "21", "data"),
                "exp": safe_get(parsed_data, "7", "data", "7", "data"),
                "cs_rank_points": safe_get(parsed_data, "7", "data", "31", "data"),
                "br_rank_points": safe_get(parsed_data, "7", "data", "15", "data"),
                "release_version": safe_get(parsed_data, "7", "data", "50", "data"),
                "account_created": datetime.fromtimestamp(
                    safe_get(parsed_data, "7", "data", "44", "data", default=0)
                ).strftime("%Y-%m-%d %I:%M:%S %p") if safe_get(parsed_data, "7", "data", "44", "data", default=0) else "N/A",
                "last_login": datetime.fromtimestamp(
                    safe_get(parsed_data, "7", "data", "24", "data", default=0)
                ).strftime("%Y-%m-%d %I:%M:%S %p") if safe_get(parsed_data, "7", "data", "24", "data", default=0) else "N/A",
            }
        }

    return {
        "player_info": player_info,
        "petInfo": pet_info,
        "guildInfo": guild_info,
    }

@routes.route("/info", methods=["GET"])
def get_player_info():
    player_id = request.args.get("uid")
    if not player_id:
        return jsonify({"message": "Player ID is required"}), 400

    try:
        data = bytes.fromhex(encrypt_api(f"08{Encrypt_ID(player_id)}1007"))
    except Exception as e:
        return jsonify({"message": f"Encryption failed: {str(e)}"}), 500

    TOKENS = get_jwt_tokens()
    if not TOKENS:
        return jsonify({"message": "No tokens found in database", "credits": "nexxlokesh"}), 500

    region_priority = ["bd", "pk", "sg", "ind","th","eu","me"]

    for region in region_priority:
        token = TOKENS.get(region)
        if not token:
            continue

        url = get_url(region)
        headers = build_headers(token)

        try:
            response = requests.post(url, headers=headers, data=data, verify=False, timeout=5)
            if response.status_code == 200:
                parsed_data = parse_response(response.content, player_id)
                if not parsed_data["player_info"]["nikname"] or parsed_data["player_info"]["nikname"] == "null":
                    continue

                result = {"data": parsed_data, "credits": "nexxlokesh", "region_used": region}
                return Response(
                    json.dumps(result, indent=2, sort_keys=False),
                    mimetype="application/json",
                )
        except Exception:
            continue

    return jsonify({"message": "Failed to retrieve valid data from prioritized regions", "credits": "nexxlokesh"}), 500
