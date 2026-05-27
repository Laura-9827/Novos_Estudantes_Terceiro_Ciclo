import runpy


if __name__ == '__main__':
    ns = runpy.run_path('app.py', run_name='__main__')
    # run_path returns a namespace; functions and constants are defined there
    df = ns['read_data']()
    q11_col = ns['find_column'](df, '1-11')
    mot = ns['code_counts'](df[q11_col], ns['Q_111']).copy()
    total_resp = int(df[q11_col].map(lambda v: bool(ns['split_codes'](v))).sum())
    total_choices = int(mot['Respostas'].sum())
    mot['pct_resp'] = mot['Respostas'] / total_resp * 100
    mot['pct_choices'] = mot['Respostas'] / total_choices * 100
    labels = ['Carreira docente no ensino superior', 'Trabalhar em investigação']
    print('total_resp=', total_resp, 'total_choices=', total_choices)
    print(mot[mot['Opção'].isin(labels)][['Opção', 'Respostas', 'pct_resp', 'pct_choices']].to_string(index=False))
