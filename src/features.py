import numpy as np

REFRAME_BASES = [
    'past3', 'head2head_percentage', 'head2head_freq',
    'mirage', 'inferno', 'nuke', 'dust2', 'overpass',
    'train', 'ancient', 'vertigo', 'anubis'
]

COUNT_BASES = [
    'wins', 'losses', 'totalwinrate', 'totallossrate',
    'online_winrate', 'lan_winrate', 'overall_winrate'
]

def reframe_winner_loser(df, col_base):
    winner_col, loser_col = f'winner_{col_base}', f'loser_{col_base}'
    team1_col, team2_col = f'team1_{col_base}', f'team2_{col_base}'
    is_team1_winner = df['winner'] == 'team1'
    df[team1_col] = np.where(is_team1_winner, df[winner_col], df[loser_col])
    df[team2_col] = np.where(is_team1_winner, df[loser_col], df[winner_col])
    return df

def build_features(df):
    """Takes a raw matches_with_elo-style DataFrame, returns df + final feature list."""
    for base in REFRAME_BASES:
        df = reframe_winner_loser(df, base)

    final_features = ['elo_diff']
    for base in REFRAME_BASES:
        diff_col = f'{base}_diff'
        df[diff_col] = df[f'team1_{base}'] - df[f'team2_{base}']
        final_features.append(diff_col)

    for base in COUNT_BASES:
        diff_col = f'{base}_diff'
        df[diff_col] = df[f'team1_{base}'] - df[f'team2_{base}']
        final_features.append(diff_col)

    df['event_type_lan'] = (df['event_type'] == 'lan').astype(int)
    final_features.append('event_type_lan')

    final_features.remove('totallossrate_diff')  # collinear, dropped

    return df, final_features