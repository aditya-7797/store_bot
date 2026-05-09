from agents.analytics import analytics_agent

state = {'query': 'show customer segments'}
res = analytics_agent(state)
print(res.get('response'))
