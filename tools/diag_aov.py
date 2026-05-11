from tools.customer_analytics import load_transactions, compute_rfm_from_transactions, build_product_price_map
import pandas as pd

print('Loading transactions...')
transactions = load_transactions()
print(f'Transactions rows: {len(transactions)}')

print('\nBuilding product price map...')
price_map = build_product_price_map()
print(f'Price map size: {len(price_map)}')
# show sample prices
sample_prices = list(price_map.items())[:10]
for pid, p in sample_prices:
    print(f'  product_id={pid}, price={p}')

print('\nComputing RFM...')
rfm = compute_rfm_from_transactions(transactions)
print(f'RFM rows: {len(rfm)}')
if rfm.empty:
    print('RFM is empty')
else:
    print('\nAverage order value overall:')
    try:
        print(' mean:', rfm['average_order_value'].mean())
        print(' median:', rfm['average_order_value'].median())
        print(' min:', rfm['average_order_value'].min())
        print(' max:', rfm['average_order_value'].max())
    except Exception as e:
        print('Could not compute stats:', e)

    print('\nTop 10 customers by average order value:')
    top = rfm.sort_values('average_order_value', ascending=False).head(10)
    print(top[['customer_id','total_purchases','total_spent_rupees','average_order_value']].to_string(index=False))

    # Show sample transactions for one top customer
    if not top.empty:
        cid = int(top.iloc[0]['customer_id'])
        print(f'\nSample transactions for customer {cid}:')
        sample_tx = transactions[transactions['customer_id'].astype(float)==float(cid)].head(20)
        print(sample_tx.head(20).to_string(index=False))
