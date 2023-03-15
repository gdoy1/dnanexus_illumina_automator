"""split a combined samplesheet into component parts for the dnanexus dna somatic pipeline"""
import argparse
from colorama import Fore, Style
import pandas as pd

panel_dict = {"RMH200ST": "RMH200V2", "RMHhaemV2": "RMHhaemV2"}


def read_samplesheet(samplesheet):
    """load combined sample sheet into dataframe"""
    df = pd.read_csv(samplesheet, sep=",", header=None).dropna(how="all")
    df.reset_index(drop=True, inplace=True)
    return df


def get_feature_index(df, feature):
    """find row index of start of given feature"""
    feature_index = df[df.iloc[:, 0] == feature].index.values[0]
    return feature_index


def check_date_format(df_head_all, date_index):
    """check to see if the date has defaulted to 00/01/1900 in the excel workbook"""
    given_date = df_head_all.iloc[date_index, 1]
    if given_date == "00/01/1900":
        print(f"{Fore.RED}Please check the date: {Style.RESET_ALL}{given_date} \U0001F612\nSampleSheets have still been created")
    else:
        print(f"SampleSheets {Fore.GREEN}created{Style.RESET_ALL}")

    
def rebuild_sub_samplesheet(df_head_all, group, assay_index, experiment_index):
    """reconstruct samplesheet with panel type and worklist"""
    df_head = df_head_all.copy()
    panel = group.iloc[0, 9]
    worklist = group.iloc[0, 12]
    # reassign values in samplesheet header
    df_head.iloc[assay_index, 1] = panel_dict[panel]
    df_head.iloc[experiment_index, 1] = worklist
    # remove worklist column
    copied_group = group.copy()
    copied_group.drop(labels="worklist", axis=1, inplace=True)
    df_ready = pd.concat([df_head, copied_group])
    outfile = f"{worklist}.{panel}.csv"
    df_ready.to_csv(outfile, sep=",", header=False, index=False)
    return df_ready


def split_samplesheet(samplesheet):
    """process combined samplesheet into sub-samplesheets"""
    # read combined sample sheet and clean NaNs
    df = read_samplesheet(samplesheet)
    # write cleaned combined samplesheet as SampleSheet.csv for demultiplex
    df.to_csv("SampleSheet.csv", sep=",", header=False, index=False)
    # get row indexes of key features
    body_index = get_feature_index(df, "Sample_ID")
    assay_index = get_feature_index(df, "Assay")
    experiment_index = get_feature_index(df, "Experiment Name")
    date_index = get_feature_index(df, "Date")
    # divide dataframe into header and body
    df_head_all = df.iloc[0 : body_index + 1, :]
    df_body_all = df.iloc[body_index + 1 :, :]
    # extract worklist from body
    copied_df_body_all = df_body_all.copy()
    copied_df_body_all["worklist"] = (
        copied_df_body_all.iloc[:, 2].str.replace("^PL", "").str.split("-").str.get(0)
    )
    # divide body by panel and worklist
    grouped = copied_df_body_all.groupby([9, "worklist"])
    groups = [grouped.get_group(x) for x in grouped.groups]
    # rebuild sub-samplesheets
    sub_sheets = []
    for group in groups:
        sub_sheets.append(rebuild_sub_samplesheet(df_head_all, group, assay_index, experiment_index))
    # check for problems with the date field (affects GAK upload)
    check_date_format(df_head_all, date_index)
    return sub_sheets


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(prog="split_somatic_samplesheet.py")
    parser.add_argument(
        "-s", "--samplesheet", type=str, help="combined all-panels sample sheet"
    )
    args = parser.parse_args()

    samplesheet = args.samplesheet

    split_samplesheet(samplesheet)
