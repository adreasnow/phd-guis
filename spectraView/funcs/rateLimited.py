import resources as r
from datetime import timedelta, datetime

def setup_df():
    global df_last_load_time
    df_last_load_time = datetime(year=1993, month=10, day=29, hour=13, minute=33)

class statusLoad_rl:
    def __init__(self, dfName, timeout: int=30) -> None:
        global df_last_load_time
        global df
        self.time_loaded = df_last_load_time
        if (datetime.now() - self.time_loaded) < timedelta(seconds=timeout) and 'df' in globals():
            self.df = df
        else:
            with r.statusLoad(dfName) as df_local:
                self.df = df_local
                df_last_load_time = datetime.now()
            df = self.df
        return

    def __enter__(self) -> None:
        return self.df
    
    def __exit__(self, a, b, c) -> None:
        return