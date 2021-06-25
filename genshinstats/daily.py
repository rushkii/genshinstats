"""Automatic sign-in for hoyolab's daily rewards.

Automatically claims the next daily reward in the daily check-in rewards.
"""
from typing import Any, Dict, Iterator, Mapping, Optional, Tuple
from urllib.parse import urljoin

from .genshinstats import fetch_endpoint
from .hoyolab import get_game_accounts
from .utils import recognize_server

__all__ = [
    'fetch_daily_endpoint', 'get_daily_reward_info', 'get_claimed_rewards', 
    'get_monthly_rewards', 'claim_daily_reward'
]

OS_URL = "https://hk4e-api-os.mihoyo.com/event/sol/" # overseas
OS_ACT_ID = "e202102251931481"
CN_URL = "https://api-takumi.mihoyo.com/event/bbs_sign_reward/" # chinese
CN_ACT_ID = "e202009291139501"

def fetch_daily_endpoint(endpoint: str, chinese: bool = False, **kwargs) -> Dict[str, Any]:
    """Fetch an enpoint for daily rewards"""
    url,act_id = (CN_URL,CN_ACT_ID) if chinese else (OS_URL,OS_ACT_ID)
    kwargs.setdefault('params',{})['act_id'] = act_id
    url = urljoin(url, endpoint)
    
    return fetch_endpoint(url, **kwargs)


def get_daily_reward_info(chinese: bool = False, cookie: Mapping[str, Any] = None) -> Tuple[bool, int]:
    """Fetches daily award info for the currently logged-in user.
    
    Returns a tuple - whether the user is logged in, how many total rewards the user has claimed so far
    """
    data = fetch_daily_endpoint("info", chinese, cookie=cookie)
    return data['is_sign'], data['total_sign_day']

_monthly_rewards = None # homebrew cache, dangerous since it should only last 1 month but who cares
def get_monthly_rewards(chinese: bool = False, lang: str = 'en-us', cookie: Mapping[str, Any] = None) -> list:
    """Gets a list of avalible rewards for the current month"""
    global _monthly_rewards
    if _monthly_rewards is None:
        _monthly_rewards = fetch_daily_endpoint(
            "home", chinese,
            cookie=cookie,
            params=dict(lang=lang)
        )['awards']
    
    return _monthly_rewards

def get_claimed_rewards(chinese: bool = False, cookie: Mapping[str, Any] = None) -> Iterator[dict]:
    """Gets all claimed awards for the currently logged-in user"""
    current_page = 1
    while True:
        data = fetch_daily_endpoint(
            "award", chinese,
            cookie=cookie,
            params=dict(current_page=current_page)
        )['list']
        yield from data
        if len(data) < 10:
            break
        current_page += 1

def claim_daily_reward(uid: int = None, chinese: bool=False, lang: str = 'en-us', cookie: Mapping[str, Any] = None) -> Optional[dict]:
    """Signs into hoyolab and claims the daily rewards.
    
    Chinese and overseas servers work a bit differently,
    so you must specify whether you want to claim rewards for chinese accounts.
    
    When claiming rewards for other users you may add a cookie argument.
    
    Returns the claimed reward or None if the reward cannot be claimed yet.
    """
    signed_in, claimed_rewards = get_daily_reward_info(chinese, cookie)
    if signed_in:
        return None
    
    # we need just one uid
    uid = uid or get_game_accounts(chinese, cookie)[0]['game_uid']
    fetch_daily_endpoint(
        "sign", chinese,
        cookie=cookie,
        method="POST",
        # these seem to no longer be required however I'm not risking it
        params=dict(uid=uid, region=recognize_server(uid), lang=lang)
    )
    rewards = get_monthly_rewards(chinese, lang, cookie)
    return rewards[claimed_rewards]
