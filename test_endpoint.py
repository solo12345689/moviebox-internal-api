
@app.get('/test_history_api')
def test_history_api(session_id: str = Cookie(None)):
    s = get_session(session_id)
    # try multiple history endpoints
    res1 = s['client'].request('GET', '/wefeed-mobile-bff/subject-api/record')
    res2 = s['client'].request('GET', '/wefeed-mobile-bff/record/list')
    res3 = s['client'].request('GET', '/history/list')
    return {
       'seeType_2': s['client'].request('GET', '/wefeed-mobile-bff/subject-api/see-list-v2', params={'seeType': '2', 'page': '1', 'pageSize': '10'}),
       'seeType_3': s['client'].request('GET', '/wefeed-mobile-bff/subject-api/see-list-v2', params={'seeType': '3', 'page': '1', 'pageSize': '10'}),
       'record_api_1': res1,
       'record_api_2': res2,
       'record_api_3': res3
    }
