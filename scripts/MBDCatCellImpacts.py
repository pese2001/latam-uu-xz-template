import numpy as np
import pandas as pd
import XZTGenerator as XZTGen

""" 
Overall summary:
With Cell Adjustments [XZTemplate_v0.csv] (Output from previous script, no 
need no to run it separately, it will be run automatically in the same script), 
MBD Numerical Distribution, MBD Type Target, VUE Impacts as input files, 
Cell-Category Parameter, and Cell-Weight Parameter as user-defined parameters, 
a series of calculations concerning MBD, Category and Cell level impacst, and 
diagnostic tests, an output is generated. This output 
(MBDCatCell_Impacts_v0.csv) will be the base Impacts worksheet for the 
Adjustments Template.

Considered steps for presentation:
7. Consider this information: Cell Adjustments [XZTemplate_v0.csv] 
   (Output from previous script),  MBD Numerical Distribution (VUE Data if 
   single-channel project, User-defined Data if multi-channel project), 
   MBD Type Target (User-defined Data), VUE Impacts (VUE Data), Cell-Category 
   Parameter (User-defined Parameter), and Cell-Weight Parameter 
   (User-defined Parameter).
8. Merges VUE Impacts with Cell Adjustments, calculates Projected Sales and 
   Impacts,  and determines Cell Relevance based on Cell-Category Parameter 
   and Cell-Weight Parameter.
9. Aggregates Cell Impacts to MBD level and calculates VUE and ADJ Sales 
   Impacts.
10. Merges MBD Impacts with MBD Numerical Distribution data.
11. Merges MBD Impacts with Type and Target Data, determines if Impacts are 
    Out of Target. Then combines MBD and Cell Impact Data to generates 
    Diagnostics for each cell category.
12. Generates output file (MBDCatCell_Impacts_v0.csv) with all results for 
    Impacts worksheet that will be feed into the macros.
"""


class MBDCCImpcts:
    """
    A class for analyzing and generating MBD (Micro Brand Development) and Cell Category impacts.

    This class processes various input data to calculate and analyze impacts on sales
    and distributions across different categories and cells.

    Attributes:
        working_dir (str): The working directory path.
        input_dir (str): The input directory path.
        output_dir (str): The output directory path.
        nspc_param (float): Parameter for NSPC calculations.
        xf_param (float): Parameter for XF calculations.
        cc_param (float): Parameter for cell category calculations.
        cw_param (float): Parameter for cell weight calculations.
        xztg (XZTGen.XZTG): An instance of the XZTG class.
        cell_adj_df (pd.DataFrame): DataFrame with cell diagnostics.
        mbd_numdist (pd.DataFrame): DataFrame with MBD numerical distribution data.
            - VUE data if single-channel project.
            - User-defined data if multi-channel project (Soon to be VUE data).
        mbd_typetarget (pd.DataFrame): DataFrame with MBD type and target data.
            - User-defined data.
        vue_impacts (pd.DataFrame): DataFrame with VUE impact data.
            - VUE data.
    """

    def __init__(self, 
                 working_dir: str,
                 nspc_param: float, 
                 xf_param: float,
                 cell_cat_param: float, 
                 cell_weight_param: float):
        """
        Initialize the MBDCCImpcts object.

        Args:
            working_dir (str): The working directory path.
            nspc_param (float): Parameter for NSPC calculations.
            xf_param (float): Parameter for XF calculations.
            cell_cat_param (float): Parameter for cell category calculations.
            cell_weight_param (float): Parameter for cell weight calculations.

        Summary:
            Sets up directory paths, parameters, initializes XZTG object, and loads input CSV files.
            
        Step-by-step:
        1. Set the working_dir attribute.
        2. Set the input_dir attribute as '{working_dir}/inputs'.
        3. Set the output_dir attribute as '{working_dir}/outputs'.
        4. Set the nspc_param attribute.
        5. Set the xf_param attribute.
        6. Set the cc_param attribute to cell_cat_param.
        7. Set the cw_param attribute to cell_weight_param.
        8. Initialize the xztg attribute with an instance of XZTGen.XZTG(working_dir).
        9. Set the cell_adj_df attribute by calling xztg.get_cell_diagnostics(nspc_param, xf_param).
        10. Load MBD_NumDist.csv into the mbd_numdist attribute.
        11. Load MBD_TypeTarget.csv into the mbd_typetarget attribute.
        12. Load VUE_Impacts.csv into the vue_impacts attribute.
        """
        self.working_dir = working_dir
        self.input_dir = f'{self.working_dir}/inputs'
        self.output_dir = f'{self.working_dir}/outputs'
        self.nspc_param = nspc_param
        self.xf_param = xf_param
        self.cc_param = cell_cat_param
        self.cw_param = cell_weight_param
        self.xztg = XZTGen.XZTG(self.working_dir)
        self.cell_adj_df = self.xztg.get_cell_diagnostics(self.nspc_param,
                                                          self.xf_param)
        self.mbd_numdist = pd.read_csv(f'{self.input_dir}/MBD_NumDist.csv')
        self.mbd_typetarget = pd.read_csv(
            f'{self.input_dir}/MBD_TypeTarget.csv')
        self.vue_impacts = pd.read_csv(f'{self.input_dir}/VUE_Impacts.csv')

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

    def cell_relevance(self, 
                       impact_col, 
                       weight_col):
        """
        Determine cell relevance based on impact and weight.

        Args:
            impact_col (float): The impact value.
            weight_col (float): The weight value.

        Returns:
            int: 1 if the cell is relevant, 0 otherwise.

        Summary:
            Checks if the absolute impact is >= cc_param and weight is >= cw_param.
        """
        if (abs(impact_col) >= self.cc_param and weight_col >= self.cw_param):
            return 1
        else:
            return 0

    def out_of_target_mbd(self, 
                          mbd_impact, 
                          mbd_target):
        """
        Check if MBD impact is out of target.

        Args:
            mbd_impact (float): The MBD impact value.
            mbd_target (float): The MBD target value.

        Returns:
            int: 1 if out of target, 0 otherwise.

        Summary:
            Compares the absolute MBD impact to the target value.
        """
        if abs(mbd_impact) >= mbd_target:
            return 1
        else:
            return 0

    def cellcat_cond(self, 
                     v1, 
                     v2):
        """
        Determine cell category condition.

        Args:
            v1 (int): First condition value.
            v2 (int): Second condition value.

        Returns:
            str: 'Anomalous' if sum of inputs >= 1, 'Normal' otherwise.

        Summary:
            Classifies the cell category based on the sum of two input conditions.
        """
        if (v1 + v2) >= 1:
            return 'Anomalous'
        else:
            return 'Normal'

    def set_cell_impacts(self):
        """
        Calculate and set cell impacts.

        Returns:
            pd.DataFrame: DataFrame with calculated cell impacts.

        Summary:
            Merges vue_impacts with cell_adj_df, calculates projected sales and impacts,
            and determines cell relevance.
        
        Step-by-step:
        1. Define columns to use (ucols) from vue_impacts.
            - 'MbdID'
            - 'MbdName'
            - 'Cell_ID'
            - 'CategoryCode'
            - 'CategoryName'
            - 'Baseline_Sales'
            - 'Baseline_CellImportance'
        2. Create a copy of vue_impacts and select only the defined columns.
        3. Create a copy of cell_adj_df and select only 'Cell_ID' and X-Factor columns.
        4. Merge the impacts and celladj DataFrames on 'Cell_ID'.
        5. Calculate new columns:
            a. 'UnprojectedSales': Baseline_Sales / BAU_XFactor (rounded to 2 decimals)
            b. 'VUE_ProjectedSales': UnprojectedSales * VUE_XFactor (rounded to 2 decimals)
            c. 'ADJ_ProjectedSales': UnprojectedSales * ADJ_XFactor (rounded to 2 decimals)
            d. 'VUE_SalesImpact': Relative change between Baseline_Sales and VUE_ProjectedSales:
                row['VUE_ProjectedSales'] / row['Baseline_Sales'] - 1
            e. 'ADJ_SalesImpact': Relative change between Baseline_Sales and ADJ_ProjectedSales:
                row['ADJ_ProjectedSales'] / row['Baseline_Sales'] - 1
        6. Add 'CellCatTest' column:
            a. Apply cell_relevance method to ADJ_SalesImpact and Baseline_CellImportance for each row:
                - Checks if the abs(row['ADJ_SalesImpact']) >= cell_cat_param.
                - Checks if row['Baseline_CellImportance'] >= cell_weight_param.
                - If both conditions are met the cell is relevant, and returns 1; otherwise returns 0.
        7. Return the final DataFrame with all calculated impacts and tests.
        """
        ucols = ['MbdID', 'MbdName', 'Cell_ID', 'CategoryCode',
                 'CategoryName', 'Baseline_Sales',
                 'Baseline_CellImportance']
        impacts = self.vue_impacts.copy()
        impacts = impacts[ucols]
        celladj = self.cell_adj_df.copy()
        celladj = celladj[['Cell_ID', 'BAU_XFactor',
                           'VUE_XFactor', 'ADJ_XFactor']]
        impact_df = pd.merge(impacts, celladj, on='Cell_ID')
        impact_df['UnprojectedSales'] = np.round(
            impact_df['Baseline_Sales'] / impact_df['BAU_XFactor'], 2)
        impact_df['VUE_ProjectedSales'] = np.round(
            impact_df['UnprojectedSales'] * impact_df['VUE_XFactor'], 2)
        impact_df['ADJ_ProjectedSales'] = np.round(
            impact_df['UnprojectedSales'] * impact_df['ADJ_XFactor'], 2)
        impact_df['VUE_SalesImpact'] = self.relative_change(
            impact_df['Baseline_Sales'], impact_df['VUE_ProjectedSales'])
        impact_df['ADJ_SalesImpact'] = self.relative_change(
            impact_df['Baseline_Sales'], impact_df['ADJ_ProjectedSales'])
        impact_df['CellCatTest'] = impact_df.apply(
            lambda row: self.cell_relevance(
                row['ADJ_SalesImpact'],
                row['Baseline_CellImportance']),
            axis=1)
        return impact_df

    def set_mbd_impacts(self):
        """
        Calculate and set MBD impacts.

        Returns:
            pd.DataFrame: DataFrame with calculated MBD impacts.

        Summary:
            Aggregates cell impacts to MBD level and calculates VUE and ADJ sales impacts.
        
        Step-by-step:
        1. Define grouping columns (gcols) for MBD level aggregation:
            - 'MbdID'
            - 'MbdName'
            - 'CategoryCode'
            - 'CategoryName'
        2. Define columns to use (ucols), including gcols and sales columns:
            - 'MbdID'
            - 'MbdName'
            - 'CategoryCode'
            - 'CategoryName'
            - 'Baseline_Sales'
            - 'VUE_ProjectedSales'
            - 'ADJ_ProjectedSales'
        3. Create a copy of the DataFrame returned by set_cell_impacts().
        4. Select only the defined columns (ucols) from the impact_df.
        5. Group the data by gcols and sum the sales columns.
        6. Reset the index of the grouped DataFrame, keeping the grouping columns.
        7. Calculate new columns:
            a. 'VUE_SalesImpact': Relative change between Baseline_Sales and VUE_ProjectedSales:
                (VUE_ProjectedSales / Baseline_Sales) - 1
            b. 'ADJ_SalesImpact': Relative change between Baseline_Sales and ADJ_ProjectedSales:
                (ADJ_ProjectedSales / Baseline_Sales) - 1
        8. Return the final DataFrame with aggregated MBD impacts.
        """
        gcols = ['MbdID', 'MbdName', 'CategoryCode',
                 'CategoryName']
        ucols = gcols + ['Baseline_Sales',
                         'VUE_ProjectedSales',
                         'ADJ_ProjectedSales']
        impact_df = self.set_cell_impacts().copy()
        impact_df = impact_df[ucols]
        impact_df = impact_df.groupby(gcols).sum()
        impact_df.reset_index(inplace=True, drop=False)
        impact_df['VUE_SalesImpact'] = self.relative_change(
            impact_df['Baseline_Sales'], impact_df['VUE_ProjectedSales'])
        impact_df['ADJ_SalesImpact'] = self.relative_change(
            impact_df['Baseline_Sales'], impact_df['ADJ_ProjectedSales'])
        return impact_df

    def set_mbd_nd(self):
        """
        Set up MBD numerical distribution data.

        Returns:
            pd.DataFrame: DataFrame with MBD impacts and numerical distribution.

        Summary:
            Merges MBD impacts with numerical distribution data.
        
        Step-by-step:
        1. Define columns to use (ucols) from mbd_numdist:
            - 'MbdID'
            - 'CategoryName'
            - 'Numerical Distribution'
        2. Create a copy of the mbd_numdist DataFrame.
        3. Select only the defined columns (ucols) from the mbd_nd DataFrame.
        4. Call set_mbd_impacts() to get the MBD impacts DataFrame.
        5. Merge the MBD impacts DataFrame with the mbd_nd DataFrame:
            - Merge on columns 'MbdID' and 'CategoryName'
        6. Return the merged DataFrame containing MBD impacts and numerical distribution data.
        """
        ucols = ['MbdID', 'CategoryName', 'Numerical Distribution']
        mbd_nd = self.mbd_numdist.copy()
        mbd_nd = mbd_nd[ucols]
        mbd_impacts = self.set_mbd_impacts()
        mbd_impact_df = pd.merge(mbd_impacts, mbd_nd,
                                 on=['MbdID', 'CategoryName'])
        return mbd_impact_df

    def set_mbd_type(self):
        """
        Set up MBD type and target data.

        Returns:
            pd.DataFrame: DataFrame with MBD impacts, types, and out-of-target flags.

        Summary:
            Merges MBD impacts with type and target data, determines if impacts are out of target,
            and saves results to a CSV file.
        
        Step-by-step:
        1. Define columns to use (ucols) from mbd_typetarget:
            - 'MbdID'
            - 'MBD Type'
            - 'Target'
        2. Create a copy of the mbd_typetarget DataFrame.
        3. Select only the defined columns (ucols) from the mbd_tt DataFrame.
        4. Call set_mbd_nd() to get the MBD impacts with numerical distribution DataFrame.
        5. Merge the impact_df (from step 4) with mbd_tt DataFrame on 'MbdID'.
        6. Add 'OutOfTarget' column:
            a. Apply out_of_target_mbd method to ADJ_SalesImpact and Target for each row:
                abs(row['ADJ_SalesImpact']) >= Target
        7. Save the resulting DataFrame to a CSV file:
            a. File path: {self.output_dir}/MBDCat_Impacts_v0.csv
            b. CSV is saved without the index column
        8. Return the final DataFrame with MBD impacts, types, and out-of-target flags.
        """
        ucols = ['MbdID', 'MBD Type', 'Target']
        mbd_tt = self.mbd_typetarget.copy()
        mbd_tt = mbd_tt[ucols]
        impact_df = self.set_mbd_nd()
        mbd_impacts = pd.merge(impact_df, mbd_tt, on='MbdID')
        mbd_impacts['OutOfTarget'] = mbd_impacts.apply(
            lambda row:
                self.out_of_target_mbd(
                    row['ADJ_SalesImpact'],
                    row['Target']),
                axis=1)
        mbd_impacts.to_csv(f'{self.output_dir}/MBDCat_Impacts_v0.csv',
                           index=False)
        return mbd_impacts

    def get_mbd_diagnostics(self):
        """
        Generate MBD and cell category diagnostics.

        Returns:
            pd.DataFrame: DataFrame with MBD and cell category diagnostics.

        Summary:
            Combines MBD and cell impact data, generates diagnostics for each cell category,
            and saves results to a CSV file.
            
        Step-by-step:
        1. Define the columns to use (ucols) for MBD and cell categories:
            - 'MbdID'
            - 'CategoryName'
            - 'OutOfTarget'
        2. Call set_mbd_type() to obtain the MBD DataFrame.
        3. Select only the defined columns (ucols) from the MBD DataFrame.
        4. Call set_cell_impacts() to obtain the cell impacts DataFrame.
        5. Merge the MBD DataFrame and the cell impacts DataFrame into cell_diag based on 'MbdID' and 'CategoryName'.
        6. Add the 'MBDCatDiag' column: 
            - Apply the cellcat_cond method to 'CellCatTest' and 'OutOfTarget' for each row:
                - 'Anomalous' if (row['CellCatTest'] + row['OutOfTarget']) >= 1, 'Normal' otherwise.
        7. Save the resulting DataFrame to a CSV file: 
            - File path: {self.output_dir}/MBDCatCell_Impacts_v0.csv 
            - The CSV is saved without the index column.
        8. Return the final DataFrame with MBD and cell category diagnostics.
        """
        ucols = ['MbdID', 'CategoryName', 'OutOfTarget']
        mbd_df = self.set_mbd_type()
        mbd_df = mbd_df[ucols]
        cell_df = self.set_cell_impacts()
        cell_diag = pd.merge(cell_df, mbd_df,
                             on=['MbdID', 'CategoryName'])
        cell_diag['MBDCatDiag'] = cell_diag.apply(
            lambda row: self.cellcat_cond(
                row['CellCatTest'],
                row['OutOfTarget']),
            axis=1)
        cell_diag.to_csv(f'{self.output_dir}/MBDCatCell_Impacts_v0.csv',
                         index=False)
        return cell_diag
