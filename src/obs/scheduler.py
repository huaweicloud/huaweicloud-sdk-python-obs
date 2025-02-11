import json
import os
import time
import requests
from obs.cache import LocalCache
import sched
from threading import Thread

cache = LocalCache(maxlen=15)


def create_auth_login_body(name, password, domain, scope):
    return {
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "domain": {"name": domain},
                        "name": name,
                        "password": password,
                    }
                },
            },
            "scope": {"project": {"name": scope}},
        }
    }


def create_security_token_body(token_id, duration_seconds):
    return {
        "auth": {
            "identity": {
                "methods": ["token"],
                "token": {
                    "id": token_id,
                    "duration_seconds": duration_seconds,
                },
            }
        }
    }


def get_X_Auth_token(name=None, password=None, domain=None, scope=None, url=None):
    name = name or os.environ.get("AUTH_NAME")
    password = password or os.environ.get("AUTH_PASSWORD")
    domain = domain or os.environ.get("AUTH_DOMAIN")
    scope = scope or os.environ.get("SCOPE")
    url = url or os.environ.get("LOGIN_URL")

    body = create_auth_login_body(name, password, domain, scope)

    headers = {"Content-Type": "application/json"}
    token = {}
    try:
        response = requests.post(
            url, headers=headers, data=json.dumps(body), timeout=10
        )
        
        if response.status_code == 201:
            x_auth_token = response.headers.get("x-subject-token")
            token = {"id": x_auth_token}
            cache.set("X-Auth-Token", token)
    except Exception as err:
        raise RuntimeError("Get X-Auth-Token err",str(err))
    return token


def refresh_shadow_tokens(url=None, endpoint=None):

    headers = {"Content-Type": "application/json"}

    endpoint = endpoint or os.environ.get("ENDPOINT")
    url = url or os.environ.get("SECURITY_TOKEN_URL")

    token = get_from_cache("X-Auth-Token")
    duration = os.environ.get("AUTH_TOKEN_EXPIRED")
    if token:
        body = create_security_token_body(token.get("id"), duration)

        response_data = {}
        try:
            response = requests.post(
                url, headers=headers, data=json.dumps(body), timeout=10
            )
            security_token = None
            response_data = {}
            if response.status_code == 201:
                response_data = response.json()
                response_data = response_data.get("credential")

                security_token = response_data.get("securitytoken")
                shadow_ak = response_data.get("access")
                shadow_sk = response_data.get("secret")
                endpoint = endpoint or response_data.get("endpoint")

                shadow_tokens = {
                    "security_token": security_token,
                    "shadow_ak": shadow_ak,
                    "shadow_sk": shadow_sk,
                    "endpoint": endpoint,
                    "expire": LocalCache.nowTime() + 6000,
                }
                cache.set("shadow_tokens", shadow_tokens)
        except Exception as err:
            raise RuntimeError("Get err when getting shadow tokens" ,str(err)) 

        return response_data
    else:
        return get_X_Auth_token()


def get_from_cache(key):
    return cache.get(key)


def start_scheduler():
    scheduler = sched.scheduler(time.time, time.sleep)

    def schedule_recurring_tasks():
        while True:
            scheduler.enter(900, 1, refresh_shadow_tokens)  
            scheduler.enter(1200, 1, get_X_Auth_token)     
            scheduler.run()

    scheduler_thread = Thread(target=schedule_recurring_tasks, daemon=True)
    scheduler_thread.start()
