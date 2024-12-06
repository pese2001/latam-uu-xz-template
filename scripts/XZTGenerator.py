import numpy as np
import pandas as pd
import re
import InputsPreCleaning as ipc

""" 
Overall summary:
With VUE Sample NSPC, Cells Last Period and Cells Chars as input files, a 
series of calculations concerning XZRatios, and diagnostic tests, an output is 
generated. This output (XZ_Template_v0.csv) will be the base  Cell Adjustments 
worksheet for the AdjustmentsTemplate.


Considered steps for presentation:
1. Consider this information: VUE Sample NSPC (VUE Data), Cells Last Period 
   (VUE Data), Cells Chars (User-defined Data).
2. Processes Cells Last Period, renames columns, merges with Cells Chars, and 
   calculates BAU_XZRatio.
3. Processes VUE Sample NSPC, renames columns, merges with BAU Cell Data, and 
   calculates VUE_XZRatio and VUE_XZDistance.
4. Adds new columns for dummy proposed distance that will be used in macros, 
   adjusted factors, and calculates various variance metrics between BAU, VUE, 
   and adjusted values.
5. Categorizes cells as Normal or Anomalous, based in a series of tests.
6. Generates output file (XZTemplate_v0.csv) with all results for CellAdj 
   worksheet that will be feed into the macros.
"""


class XZTG:
    """
    A class for processing and analyzing cell data.

    This class handles the loading, transformation, and analysis of cell data
    from various input files. It performs calculations on BAU and VUE data, 
    and generates diagnostic information for cells.

    Attributes:
        working_dir (str): The working directory path.
        input_dir (str): The input directory path.
        output_dir (str): The output directory path.
        cells_chars (pd.DataFrame): DataFrame containing cell characteristics.
            - User-defined data.
        cells_lastperiod (pd.DataFrame): DataFrame containing last period cell data.
            - VUE data.
        vue_samplenspc (pd.DataFrame): DataFrame containing VUE sample NSPC data.
            - VUE data.
    """

    def __init__(self, 
                 working_dir: str):
        """
        Initialize the XZTG object.

        Args:
            working_dir (str): The working directory path.

        Summary:
            Sets up directory paths and loads input CSV files into DataFrames.
        """
        ipc.CleaningInputs(working_dir).get_clean_csvs()
        self.working_dir = working_dir
        self.input_dir = f'{self.working_dir}/inputs'
        self.output_dir = f'{self.working_dir}/outputs'
        self.cells_chars = pd.read_csv(f'{self.input_dir}/Cells_Chars.csv')
        self.cells_lastperiod = pd.read_csv(
            f'{self.input_dir}/Cells_LastPeriod.csv')
        self.vue_samplenspc = pd.read_csv(
            f'{self.input_dir}/VUE_SampleNSPC.csv')

    def set_bau_cells(self):
        """
        Set up BAU cell data.

        Returns:
            pd.DataFrame: DataFrame containing BAU cell data with calculated XZRatio.

        Summary:
            Processes cells_lastperiod DataFrame, renames columns, merges with
            cells_chars, and calculates BAU_XZRatio.
            
        Step-by-step:
        1. Create a copy of the cells_lastperiod DataFrame.
        2. Filter out 'Period' and 'Condition' columns from the copied DataFrame.
        3. Rename columns to prefix 'BAU_' to all except 'Cell_ID' and 'Cell_Name'.
        4. Create a copy of the cells_chars DataFrame.
        5. Merge the processed cells_lastperiod with cells_chars on 'Cell_ID'.
        6. Calculate 'BAU_XZRatio' by dividing 'BAU_XFactor' by 'BAU_ZFactor'.
        7. Return the resulting DataFrame.
        """
        cells_lp = self.cells_lastperiod.copy()
        cells_lp = cells_lp[[
            x for x in cells_lp.columns.unique().tolist()
            if x not in ['Period', 'Condition']]]
        cells_lp.rename(
            columns={x: f'BAU_{x}' for x in cells_lp.columns.unique().tolist()
                     if x not in ['Cell_ID', 'Cell_Name']},
            inplace=True)
        cells_ch = self.cells_chars.copy()
        cells_df = pd.merge(cells_ch, cells_lp, on='Cell_ID')
        cells_df['BAU_XZRatio'] = cells_df['BAU_XFactor'] / \
            cells_df['BAU_ZFactor']
        return cells_df
    
    def get_handler_value(self,
                          cell_name):
        """
        Determine the handler value based on the cell name.

        Args:
            cell_name (str): The name of the cell.

        Returns:
            int: 0 if the cell name contains specific patterns, 1 otherwise.

        Summary:
            Checks if the cell name contains any of the patterns '_NM', '_NO_MANEJANTE', or 'NOMANEJANTE'.
            Returns 0 if a pattern is found, 1 otherwise.
        """
        patterns = ['_NM', '_NO_MANEJANTE', 'NOMANEJANTE', 'NO MANEJANTE']
        combined_pattern = '|'.join(map(re.escape, patterns))
        if re.search(combined_pattern, cell_name):
            return 0
        else:
            return 1

    def set_vue_cells(self):
        """
        Set up VUE cell data.

        Returns:
            pd.DataFrame: DataFrame containing merged BAU and VUE cell data with
                          additional calculated fields.

        Summary:
            Processes vue_samplenspc DataFrame, renames columns, merges with BAU
            cell data, and calculates VUE_XZRatio and VUE_XZDistance.
        
        Step-by-step:
        1. Call set_bau_cells() to get the BAU cell data.
        2. Create a copy of the vue_samplenspc DataFrame.
        3. Select specific columns from vue_nspc:
            - 'IBD Name'
            - 'IBD ID'
            - 'Cell ID'
            - 'X Universe'
            - 'Z Universe' 
            - 'X Panel'
            - 'Z Panel'
            - 'X Factor'
            - 'Z Factor'
        4. Rename columns:
            a. Replace spaces with underscores for 'IBD Name', 'IBD ID', and 'Cell ID'.
            b. Remove spaces from other column names.
            c. Prefix 'VUE_' to all columns except 'IBD_Name', 'IBD_ID', and 'Cell_ID'.
        5. Merge the processed vue_nspc with the BAU cell data on 'Cell_ID'.
        6. Calculate 'VUE_XZRatio' by dividing 'VUE_XFactor' by 'VUE_ZFactor'.
        7. Calculate 'VUE_XZDistance' using the formula:
            (1 - (VUE_ZFactor / VUE_XFactor)) * sqrt(VUE_ZPanel)
        8. Select and reorder specific columns in the final DataFrame:
            - 'INDEX'
            - 'CHANNEL'
            - 'SAMPLE'
            - 'IBD_ID'
            - 'IBD_Name'
            - 'Cell_ID'
            - 'Cell_Name',
            - 'NielsenArea'
            - 'StoreTypeChannel'
            - 'StoreType'
            - 'BAU_XPanel'
            - 'BAU_ZPanel'
            - 'BAU_XUniverse'
            - 'BAU_ZUniverse'
            - 'BAU_XFactor'
            - 'BAU_ZFactor'
            - 'BAU_XZRatio'
            - 'VUE_XUniverse'
            - 'VUE_ZUniverse'
            - 'VUE_XPanel'
            - 'VUE_ZPanel'
            - 'VUE_XFactor'
            - 'VUE_ZFactor'
            - 'VUE_XZRatio'
            - 'VUE_XZDistance'
        9. Return the resulting DataFrame.
        """
        cells_df = self.set_bau_cells()
        vue_nspc = self.vue_samplenspc.copy()
        ucols = ['IBD Name',
                 'IBD ID',
                 'Cell ID',
                 'X Universe',
                 'Z Universe',
                 'X Panel',
                 'Z Panel',
                 'X Factor',
                 'Z Factor']
        vue_nspc = vue_nspc[ucols]
        vue_nspc.rename(columns={x: x.replace(' ', '_')
                                 for x in vue_nspc.columns.unique().tolist()
                                 if x in ['IBD Name', 'IBD ID', 'Cell ID']},
                        inplace=True)
        vue_nspc.rename(columns={x: x.replace(' ', '')
                                 for x in vue_nspc.columns.unique().tolist()
                                 if x not in [
                                     'IBD_Name', 'IBD_ID', 'Cell_ID']},
                        inplace=True)
        vue_nspc.rename(columns={x: f'VUE_{x}'
                                 for x in vue_nspc.columns.unique().tolist()
                                 if x not in [
                                     'IBD_Name', 'IBD_ID', 'Cell_ID']},
                        inplace=True)
        cells = pd.merge(cells_df, vue_nspc, on='Cell_ID')
        cells['VUE_XZRatio'] = np.round(
            cells['VUE_XFactor'] / cells['VUE_ZFactor'], 4)
        cells['VUE_XZDistance'] = np.round((
            1 - (cells['VUE_ZFactor'] / cells['VUE_XFactor']))*np.sqrt(
                cells['VUE_ZPanel']), 4) 
        cells['Handler'] = cells.apply(lambda row: self.get_handler_value(
            row['Cell_Name']), axis=1)
        cells = cells[['INDEX', 
                       'CHANNEL',
                       'SAMPLE',
                       'IBD_ID',
                       'IBD_Name',
                       'Cell_ID',
                       'Cell_Name',
                       'NielsenArea',
                       'StoreTypeChannel',
                       'StoreType',
                       'Handler',
                       'BAU_XPanel',
                       'BAU_ZPanel',
                       'BAU_XUniverse',
                       'BAU_ZUniverse',
                       'BAU_XFactor',
                       'BAU_ZFactor',
                       'BAU_XZRatio',
                       'VUE_XUniverse',
                       'VUE_ZUniverse',
                       'VUE_XPanel',
                       'VUE_ZPanel',
                       'VUE_XFactor',
                       'VUE_ZFactor',
                       'VUE_XZRatio',
                       'VUE_XZDistance']]
        return cells

    def relative_change(self, 
                        v1, 
                        v2):
        """
        Calculate the relative change between two values.

        Args:
            v1 (float): The first value.
            v2 (float): The second value.

        Returns:
            float: The relative change, rounded to 4 decimal places.

        Summary:
            Calculates (v2 / v1) - 1 and rounds to 4 decimal places.
        """
        rch = np.round((v2 / v1) - 1, 4)
        return rch

    def dtest(self,
              c1,
              distance):
        """
        Perform a distance test on a given value.

        Args:
            c1 (float): The value to test.
            distance_param (float): Parameter for Distance test.

        Returns:
            int: 0 if the absolute value of c1 is less than or equal to distance_param, 1 otherwise.

        Summary:
            Checks if the absolute value of c1 is within the range [-distance_param, distance_param].
        """
        if abs(c1) <= distance:
            return 0
        else:
            return 1

    def var_test(self, 
                 var_col, 
                 param: float):
        """
        Perform a variance test on a given value.

        Args:
            var_col (float): The value to test.
            param (float): The threshold parameter.

        Returns:
            int: 0 if the absolute value of var_col is less than param, 1 otherwise.

        Summary:
            Checks if the absolute value of var_col is less than the given parameter.
        """
        if abs(var_col) < param:
            return 0
        else:
            return 1

    def sign_test(self, 
                  v1, 
                  v2):
        """
        Perform a sign test on two values.

        Args:
            v1 (float): The first value.
            v2 (float): The second value.

        Returns:
            int: 0 if the signs are the same, 1 if they are different.

        Summary:
            Compares the signs of v1 and v2, handling cases where one or both values are zero.
        """
        if v2 != 0:
            if np.sign(v1/v2) == 1:
                return 0
            else:
                return 1
        elif (v2 == 0 and v1 != 0):
            if np.sign(v2/v1) == 1:
                return 0
            else:
                return 1
        else:
            return 0

    def cell_cond(self, 
                  v1, 
                  v2, 
                  v3, 
                  v4):
        """
        Determine the cell condition based on four input values.

        Args:
            v1 (int): First test result.
            v2 (int): Second test result.
            v3 (int): Third test result.
            v4 (int): Fourth test result.

        Returns:
            str: 'Anomalous' if the sum of inputs is 2 or greater, 'Normal' otherwise.

        Summary:
            Sums the input values and classifies the cell as 'Anomalous' or 'Normal'.
        """
        if (v1 + v2 + v3 + v4) >= 2:
            return 'Anomalous'
        else:
            return 'Normal'

    def set_dummy_calc(self):
        """
        Perform dummy calculations on cell data.

        Returns:
            pd.DataFrame: DataFrame with additional calculated fields.

        Summary:
            Adds new columns for proposed distance, adjusted factors, and calculates
            various variance metrics between BAU, VUE, and adjusted values.
        
        Step-by-step:
        1. Call set_vue_cells() to get the VUE cell data.
        2. Add new columns:
            a. 'XZ Proposed Distance': Set to VUE_XZDistance
            b. 'ADJ_XFactor': Set to VUE_XFactor
            c. 'ADJ_XUniverse': Set to VUE_XUniverse
            d. 'ADJ_XPanel': Set to VUE_XPanel
        3. Calculate variance metrics:
            a. 'VAR_XUniverse (BAU vs VUE)': Relative change between BAU_XUniverse and VUE_XUniverse:
                (VUE_XUniverse / BAU_XUniverse) - 1
            b. 'VAR_XUniverse (BAU vs ADJ)': Relative change between BAU_XUniverse and ADJ_XUniverse:
                (ADJ_XUniverse / BAU_XUniverse) - 1
            c. 'VAR_XFactor (BAU vs VUE)': Relative change between BAU_XFactor and VUE_XFactor:
                (VUE_XFactor / BAU_XFactor) - 1
            d. 'VAR_XFactor (BAU vs ADJ)': Relative change between BAU_XFactor and ADJ_XFactor:
                (ADJ_XFactor / BAU_XFactor) - 1
            e. 'VAR_ZUniverse': Relative change between BAU_ZUniverse and VUE_ZUniverse:
                (VUE_ZUniverse / BAU_ZUniverse) - 1
        4. Add 'Change in XPanel' column:
            Compare VUE_XPanel and ADJ_XPanel using bool_comparisson method for each row:
                True if the values are different, False if they are the same.
        5. Return the updated DataFrame with all new columns and calculations.
        """
        cells_df = self.set_vue_cells()
        cells_df['XZ Proposed Distance'] = cells_df['VUE_XZDistance']
        cells_df['ADJ_XFactor'] = cells_df['VUE_XFactor']
        cells_df['ADJ_XUniverse'] = cells_df['VUE_XUniverse']
        cells_df['VAR_XUniverse (BAU vs VUE)'] = self.relative_change(
            cells_df['BAU_XUniverse'], cells_df['VUE_XUniverse'])
        cells_df['VAR_XUniverse (BAU vs ADJ)'] = self.relative_change(
            cells_df['BAU_XUniverse'], cells_df['ADJ_XUniverse'])
        cells_df['VAR_XFactor (BAU vs VUE)'] = self.relative_change(
            cells_df['BAU_XFactor'], cells_df['VUE_XFactor'])
        cells_df['VAR_XFactor (BAU vs ADJ)'] = self.relative_change(
            cells_df['BAU_XFactor'], cells_df['ADJ_XFactor'])
        cells_df['VAR_ZUniverse'] = self.relative_change(
            cells_df['BAU_ZUniverse'], cells_df['VUE_ZUniverse'])
        return cells_df
    
    def area_channel_weight(self,
                            row,
                            df,
                            target_column_name):
        """
        Calculate the area-channel weight for a given row.

        Args:
            row (pd.Series): A row from the DataFrame.
            df (pd.DataFrame): The entire DataFrame.
            target_column_name (str): The name of the target column for calculations.

        Returns:
            float: The calculated area-channel weight.

        Summary:
            Calculates the weight based on the Handler value and the ratio of the target column
            value to the sum of target column values for matching rows.
        """
        if row['Handler'] == 1:
            mask = (df['Handler'] == 1) & \
                (df['StoreTypeChannel'] == row['StoreTypeChannel']) & \
                (df['NielsenArea'] == row['NielsenArea'])
            sum_target = df.loc[mask, target_column_name].sum()
            if sum_target != 0:
                return row[target_column_name] / sum_target
            else:
                return 0
        else:
            return 0

    def set_cell_area_channel_weights(self):
        """
        Set area-channel weights for different scenarios.

        Returns:
            pd.DataFrame: DataFrame with added area-channel weight columns.

        Summary:
            Calculates and adds columns for BAU, VUE, and ADJ area-channel weights
            for both N and NSPC scenarios.
        """
        cells_df = self.set_dummy_calc()
        cells_df['BAU_N Area-Channel Cell Weight'] = cells_df.apply(lambda row: 
            self.area_channel_weight(row, cells_df, 'BAU_ZUniverse'), axis=1)
        cells_df['BAU_NSPC Area-Channel Cell Weight'] = cells_df.apply(lambda row: 
            self.area_channel_weight(row, cells_df, 'BAU_XUniverse'), axis=1)
        cells_df['VUE_N Area-Channel Cell Weight'] = cells_df.apply(lambda row: 
            self.area_channel_weight(row, cells_df, 'VUE_ZUniverse'), axis=1)
        cells_df['VUE_NSPC Area-Channel Cell Weight'] = cells_df.apply(lambda row: 
            self.area_channel_weight(row, cells_df, 'VUE_XUniverse'), axis=1)
        cells_df['ADJ_NSPC Area-Channel Cell Weight'] = cells_df.apply(lambda row: 
            self.area_channel_weight(row, cells_df, 'ADJ_XUniverse'), axis=1)
        return cells_df
    
    def set_cell_area_channel_weight_diff(self):
        """
        Calculate differences between area-channel weights.

        Returns:
            pd.DataFrame: DataFrame with added weight difference columns.

        Summary:
            Computes and adds columns for the differences between BAU, VUE, and ADJ
            area-channel weights for both N and NSPC scenarios.
        """
        cells_df = self.set_cell_area_channel_weights()
        cells_df['N Area-Channel Cell Weight diff (BAU vs VUE)'] = (
            cells_df['BAU_N Area-Channel Cell Weight'] 
            - cells_df['VUE_N Area-Channel Cell Weight'])
        cells_df['NSPC Area-Channel Cell Weight diff (BAU vs VUE)'] = (
            cells_df['BAU_NSPC Area-Channel Cell Weight'] 
            - cells_df['VUE_NSPC Area-Channel Cell Weight'])
        cells_df['NSPC Area-Channel Cell Weight diff (BAU vs ADJ)'] = (
            cells_df['BAU_NSPC Area-Channel Cell Weight'] 
            - cells_df['ADJ_NSPC Area-Channel Cell Weight'])
        cells_df['NSPC Area-Channel Cell Weight diff (VUE vs ADJ)'] = (
            cells_df['VUE_NSPC Area-Channel Cell Weight'] 
            - cells_df['ADJ_NSPC Area-Channel Cell Weight'])
        return cells_df
    
    def average_x_vs_z(self, 
                       x_column,
                       z_column):
        """
        Calculate the average ratio between X and Z columns.

        Args:
            x_column (pd.Series): The X column values.
            z_column (pd.Series): The Z column values.

        Returns:
            float: The rounded average ratio of X to Z.

        Summary:
            Computes the ratio of X to Z columns and rounds the result to 3 decimal places.
        """
        avrg = np.round((x_column / z_column), 3)
        return avrg
    
    def set_bau_vue_averages(self):
        """
        Set average values for BAU, VUE, and ADJ scenarios.

        Returns:
            pd.DataFrame: DataFrame with added average columns.

        Summary:
            Calculates and adds columns for average Universe and Panel values
            for BAU, VUE, and ADJ scenarios.
        """
        cells_df = self.set_cell_area_channel_weight_diff()
        cells_df['Average BAU Universe'] = cells_df.apply(lambda row:
            self.average_x_vs_z(row['BAU_XUniverse'], row['BAU_ZUniverse']), axis=1)
        cells_df['Average BAU Panel'] = cells_df.apply(lambda row:
            self.average_x_vs_z(row['BAU_XPanel'], row['BAU_ZPanel']), axis=1)
        cells_df['Average VUE Universe'] = cells_df.apply(lambda row:
            self.average_x_vs_z(row['VUE_XUniverse'], row['VUE_ZUniverse']), axis=1)
        cells_df['Average VUE Panel'] = cells_df.apply(lambda row:
            self.average_x_vs_z(row['VUE_XPanel'], row['VUE_ZPanel']), axis=1)
        cells_df['Average ADJ Universe'] = cells_df.apply(lambda row:
            self.average_x_vs_z(row['ADJ_XUniverse'], row['VUE_ZUniverse']), axis=1)
        return cells_df

    def set_cell_flags(self, 
                       distance_param: float,
                       nspc_param: float, 
                       xf_param: float):
        """
        Set cell flags based on various tests.

        Args:
            distance_param (float): Parameter for Distance test.
            nspc_param (float): Parameter for NSPC test.
            xf_param (float): Parameter for XF test.

        Returns:
            pd.DataFrame: DataFrame with added test result columns.

        Summary:
            Applies dtest, var_test, and sign_test to set flags for each cell.
            
        Step-by-step:
        1. Call set_dummy_calc() to get the DataFrame with dummy calculations.
        2. Add 'DTest' column:
            a. Apply dtest method to 'VUE_XZDistance' for each row:
                0 if the abs(row['VUE_XZDistance']) <= 3, 1 otherwise.
        3. Add 'NSPCTest' column:
            a. Apply var_test method to 'VAR_XUniverse (BAU vs ADJ)' using nspc_param for each row:
                0 if abs(row['VAR_XUniverse (BAU vs ADJ)']) <= nspc_param, 1 otherwise.
        4. Add 'XFTest' column:
            a. Apply var_test method to 'VAR_XFactor (BAU vs ADJ)' using xf_param for each row:
                0 if abs(row['VAR_XFactor (BAU vs ADJ)']) <= nspc_param, 1 otherwise.
        5. Add 'SignTest' column:
            a. Apply sign_test method to 'VAR_XUniverse (BAU vs ADJ)' and 'VAR_ZUniverse' for each row:
                0 if the signs of row['VAR_XUniverse (BAU vs ADJ)'] and row['VAR_ZUniverse'] are the same, 1 if they are different.
        6. Return the updated DataFrame with all new test result columns.
        """
        cells_df = self.set_bau_vue_averages()
        cells_df['DTest'] = cells_df.apply(lambda row: self.dtest(
            row['VUE_XZDistance'], distance_param), axis=1)
        cells_df['NSPCTest'] = cells_df.apply(lambda row: self.var_test(
            row['VAR_XUniverse (BAU vs ADJ)'], nspc_param), axis=1)
        cells_df['XFTest'] = cells_df.apply(lambda row: self.var_test(
            row['VAR_XFactor (BAU vs ADJ)'], xf_param), axis=1)
        cells_df['SignTest'] = cells_df.apply(lambda row: self.sign_test(
            row['VAR_XUniverse (BAU vs ADJ)'], row['VAR_ZUniverse']),
            axis=1)
        return cells_df

    def get_cell_diagnostics(self, 
                             distance_param: float,
                             nspc_param: float, 
                             xf_param: float):
        """
        Generate cell diagnostics and save results to a CSV file.

        Args:
            distance_param (float): Parameter for Distance test.
            nspc_param (float): Parameter for NSPC test.
            xf_param (float): Parameter for XF test.

        Returns:
            pd.DataFrame: DataFrame with cell diagnostics.

        Summary:
            Calls set_cell_flags, determines cell condition, and saves the result
            to a CSV file in the output directory.
            
        Step-by-step:
        1. Call set_cell_flags(nspc_param, xf_param) to get the DataFrame with cell flags.
        2. Add 'CellDiagnostic' column:
            - Apply cell_cond method to 'DTest', 'NSPCTest', 'XFTest', and 'SignTest' for each row:
                - Sums row['DTest']. row['NSPCTest'], row['XFTest'], row['SignTest'].
                - Classifies the cell as 'Anomalous' if the sum of inputs is 2 or greater, 'Normal' otherwise.
        3. Save the resulting DataFrame to a CSV file:
            - File path: {self.output_dir}/XZTemplate_v0.csv
            - CSV is saved without the index column.
        4. Return the final DataFrame with all diagnostics.
        """
        cells_df = self.set_cell_flags(distance_param, nspc_param, xf_param)
        cells_df['CellDiagnostic'] = cells_df.apply(lambda row: self.cell_cond(
            row['DTest'], row['NSPCTest'], row['XFTest'], row['SignTest']),
            axis=1)
        cells_df.to_csv(f'{self.output_dir}/XZTemplate_v0.csv',
                        index=False)
        return cells_df
