import os
import re
import pandas as pd
import unidecode

cell_char_columns = ['INDEX',
                     'CHANNEL',
                     'SAMPLE',
                     'Cell_ID',
                     'StoreTypeChannel',
                     'NielsenArea',
                     'StoreType']

cell_last_period_columns = ['Period',
                            'Cell_ID',
                            'Cell_Name',
                            'XPanel',
                            'ZPanel',
                            'XUniverse',
                            'ZUniverse',
                            'XFactor',
                            'ZFactor',
                            'Condition']

mbd_numb_dist_columns = ['MbdID',
                         'INDEX',
                         'MbdName',
                         'CategoryName',
                         'Numerical Distribution']

mbd_type_target = ['MbdID',
                   'INDEX',
                   'MbdName',
                   'MBD Type',
                   'Target']

vue_impacts_columns = ['PeriodId',
                       'PeriodName',
                       'ReportingGroupID',
                       'ReportingGroupName',
                       'MbdOrder',
                       'MbdID',
                       'MbdName',
                       'Cell_ID',
                       'CellName',
                       'CategoryCode',
                       'CategoryName',
                       'ProductSegmentLevel',
                       'productsegmentname',
                       'Baseline_Sales',
                       'Baseline_CellImportance',
                       'NSPC_W1_Sales',
                       'NSPC_W1_Baseline_Impact',
                       'NSPC_W1_CellImportance']

vue_sample_nspc_impact = ['Period',
                          'Period_Nm',
                          'Sample_ID',
                          'Sample_Nm',
                          'Cell ID',
                          'Cell_Name',
                          'Cell_Condition',
                          'X Universe',
                          'Z Universe',
                          'X Panel',
                          'Z Panel',
                          'X Factor',
                          'Z Factor',
                          'XZ_Ratio',
                          'IBD ID',
                          'IBD Name']

input_files_names = ['Cells_Chars.csv',
                     'Cells_LastPeriod.csv',
                     'MBD_NumDist.csv',
                     'MBD_TypeTarget.csv',
                     'VUE_Impacts.csv',
                     'VUE_SampleNSPC.csv']

file_columns_dict = {'Cells_Chars.csv': cell_char_columns,
                     'Cells_LastPeriod.csv': cell_last_period_columns,
                     'MBD_NumDist.csv': mbd_numb_dist_columns,
                     'MBD_TypeTarget.csv': mbd_type_target,
                     'VUE_Impacts.csv': vue_impacts_columns,
                     'VUE_SampleNSPC.csv': vue_sample_nspc_impact}

numerical_cols_dict = {'Cell_ID': int,
                       'Period': int,
                       'XPanel': int,
                       'ZPanel': int,
                       'XUniverse': int,
                       'ZUniverse': int,
                       'XFactor': float,
                       'ZFactor': float,
                       'Numerical Distribution': float,
                       'Target': float,
                       'PeriodId': int,
                       'MbdOrder': int,
                       'CategoryCode': int,
                       'Baseline_Sales': float,
                       'Baseline_CellImportance': float,
                       'NSPC_W1_Sales': float,
                       'NSPC_W1_Baseline_Impact': float,
                       'NSPC_W1_CellImportance': float,
                       'X Universe': int,
                       'Z Universe': int,
                       'X Panel': int,
                       'Z Panel': int,
                       'X Factor': float,
                       'Z Factor': float,
                       'XZ_Ratio': float}


class CleaningInputs:
    
    def __init__(self,
                 working_dir: str):
        self.inputs_path = f'{working_dir}/inputs'
        
    def _list_files(self):
        csv_list = [file for file in os.listdir(self.inputs_path) if file.endswith('.csv')]
        return csv_list
    
    def _list_filename_error_list(self):
        csv_list = self._list_files()
        filename_error_list = [file for file in csv_list if file not in input_files_names]
        return filename_error_list
    
    def _filename_error_logs(self):
        csv_list = self._list_files()
        if len(self._list_filename_error_list()) > 0:
            print('The following files do not have the proper name:')
            for file in self._list_filename_error_list():
                print('\t', file)
            print('The proper names are:')
            for input_files_name in input_files_names:
                print('\t', input_files_name)
            raise ValueError('Please rename the files with the proper names.')
        return csv_list
        
    def _column_error_logs(self, df: pd.DataFrame, columns: list):
        df_columns = df.columns.tolist()
        column_error_list = [col for col in df_columns if col not in columns]
        if len(column_error_list) > 0:
            print('The following columns are not in the dataframe:')
            for column in column_error_list:
                print('\t', column)
            print('The proper columns are:')
            for column in columns:
                print('\t', column)
            raise ValueError('Please check the columns in the dataframe.')
        
    def _df_columns(self, filename: str):
        return file_columns_dict[filename]
        
    def _csvs_errors(self):
        csv_list = self._filename_error_logs()
        dfs_list = []
        for csv in csv_list:
            df = pd.read_csv(f'{self.inputs_path}/{csv}')
            self._column_error_logs(df, self._df_columns(csv))
            dfs_list.append(df)
        return dfs_list
    
    def _set_col_type_num(self, df: pd.DataFrame, target_cols: list):
        for target_col in target_cols:
            df[target_col] = df[target_col].astype(numerical_cols_dict[target_col])
        return df
    
    def _set_col_type_str(self, df: pd.DataFrame, object_cols: list):
        for object_col in object_cols:
            df[object_col] = df[object_col].astype(str)
        return df
    
    def _clean_encoding_text(self, text):
        return unidecode.unidecode(str(text))
    
    def _process_mbd_code_row(self, code):
        code_str = str(code)
        return code_str.split('_')[-1]
    
    def _process_mbd_code_df(self, df: pd.DataFrame):
        if 'MbdID' in df.columns:
            df['MbdID'] = df['MbdID'].apply(lambda x: self._process_mbd_code_row(x))
        return df
            
    
    def _clean_encoding_df(self, df: pd.DataFrame, object_cols: list):
        for object_col in object_cols:
            df[object_col] = df[object_col].apply(
                lambda x: self._clean_encoding_text(str(x)) if pd.notna(x) else x
            )
        return df
        
    def _get_clean_csv_list(self):
        dfs_list = self._csvs_errors()
        for df in dfs_list:
            target_cols = [col for col in df.columns if col in numerical_cols_dict.keys()]
            object_cols = [col for col in df.columns if col not in target_cols]
            self._set_col_type_num(df, target_cols)
            self._set_col_type_str(df, object_cols)
            self._clean_encoding_df(df, object_cols)
        return dfs_list        
    
    def get_clean_csvs(self):
        dfs_list = self._get_clean_csv_list()
        csv_list = self._list_files()
        for i in range(0, len(dfs_list)):
            df = dfs_list[i]
            df = self._process_mbd_code_df(df)
            df.to_csv(f'{self.inputs_path}/{csv_list[i]}', index=False)
            
    
    