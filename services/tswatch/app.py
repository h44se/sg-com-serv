import os
import ts3
from flask import Flask, jsonify

app = Flask(__name__)

TS3_QUERY_USER = os.getenv("TS3_QUERY_USER", "serveradmin")
TS3_QUERY_PASSWORD = os.getenv("TS3_QUERY_PASSWORD")
TS3_QUERY_IP = os.getenv("TS3_QUERY_IP", "teamspeak3")
TS3_QUERY_PORT = int(os.getenv("TS3_QUERY_PORT", 10011))
TS3_SERVER_ID = int(os.getenv("TS3_SERVER_ID", 1))

@app.route("/status")
def get_status():
    try:
        # Connect using telnet protocol as it is standard for TS3 Query
        with ts3.query.TS3ServerConnection(f"telnet://{TS3_QUERY_IP}:{TS3_QUERY_PORT}") as ts3conn:
            ts3conn.exec_("login", client_login_name=TS3_QUERY_USER, client_login_password=TS3_QUERY_PASSWORD)
            ts3conn.exec_("use", sid=TS3_SERVER_ID)
            
            # Get server info
            serverinfo = ts3conn.exec_("serverinfo").parsed[0]
            max_users = int(serverinfo["virtualserver_maxclients"])
            
            # Get clients and filter for real users (client_type=0)
            clients = ts3conn.exec_("clientlist").parsed
            connected_users = len([c for c in clients if c.get("client_type") == "0"])
            
            return jsonify({
                "users": connected_users,
                "max_users": max_users,
                "status": "online"
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "users": 0,
            "max_users": 0
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
