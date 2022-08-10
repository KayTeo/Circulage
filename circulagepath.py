import pandas as pd

# Note on some jargon:
# A hop refers to a single trade between a pair of cryptocurrencies

one_hop_matrix = pd.DataFrame({
    'source' : ['A', 'B', 'C', 'D'],
    'A' : [1, 0.5, 0.25, 0.1],
    'B' : [2, 1, 0.5, 0.2],
    'C' : [4, 2, 1, 0.2],
    'D' : [10, 5, 5, 1]
})
one_hop_matrix.set_index('source', inplace= True)

profit_path = pd.DataFrame({
    'source' : ['A', 'B', 'C', 'D'],
    'A' : [[], [], [], []],
    'B' : [[], [], [], []],
    'C' : [[], [], [], []],
    'D' : [[], [], [], []]
})
profit_path.set_index('source', inplace= True)

for source in list(profit_path.index):
    for dest in profit_path.columns:
        profit_path[dest].loc[source] = [source, dest] # Setting the initial path (<= 1 hop) between all tokens

loss_path = profit_path.copy() 

tokens = list(one_hop_matrix.index)

n = 5
profit_df = one_hop_matrix.copy()
loss_df = one_hop_matrix.copy()
i = 2
# i is the number of "hops"
# s = source, m = middle point, d = destination
while i < n:
    # Copying into separate df to avoid taking current state into calculation
    new_profit_df = profit_df.copy()
    new_loss_df = loss_df.copy()
    new_profit_path = profit_path.copy()
    new_loss_path = loss_path.copy()
    for s in tokens:
        for d in tokens:
            for m in tokens:
                # Calculating the best case
                s_to_d = profit_df[d].loc[s]
                s_to_m = profit_df[m].loc[s]
                m_to_d = one_hop_matrix[d].loc[m]
                if s_to_m * m_to_d > s_to_d:
                    s_to_m_path = profit_path[m].loc[s]
                    m_to_d_path = profit_path[d].loc[m]
                    new_profit_path[d].loc[s] = s_to_m_path + m_to_d_path[1 : ]
                    new_profit_df[d].loc[s] = s_to_m * m_to_d
                # Calculating the worst case
                s_to_d = loss_df[d].loc[s]
                s_to_m = loss_df[m].loc[s]
                m_to_d = loss_df[d].loc[m]
                if s_to_m * m_to_d < s_to_d:
                    s_to_m_path = loss_path[m].loc[s]
                    m_to_d_path = loss_path[d].loc[m]
                    new_loss_path[d].loc[s] = s_to_m_path + m_to_d_path [1 : ]
                    new_loss_df[d].loc[s] = s_to_m * m_to_d
    profit_df = new_profit_df
    loss_df = new_loss_df
    profit_path = new_profit_path
    loss_path = new_loss_path
    i += 1

circulage_path : list

highest = 0
print(profit_path)
print(loss_path)

for s in tokens:
    for d in tokens:
        profit = profit_df[d].loc[s]
        loss = loss_df[d].loc[s]
        if profit // loss > highest:
            highest = profit // loss
            circulage_path = profit_path[d].loc[s] + ((loss_path[d].loc[s])[::-1])[1 : ]

print(circulage_path)
print(highest)
