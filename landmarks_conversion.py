#!/usr/bin/env python
# coding: utf-8

import os
import argparse
import platform
import pandas as pd
import numpy as np


def get_landmarks_per_individual(df, unique_individuals):
    landmarks_per_individual = [0 for _ in range(len(unique_individuals))]
    for i in df['individual']:
        for u in unique_individuals:
            if int(i) == int(u):
                landmarks_per_individual[int(u)-1] += 1
    return landmarks_per_individual    

def create_columns(how_many=1):
    #Creates as many columns x, y, z (with numbers) as indicated by `how_many` argument. 
    template = ['x', 'y', 'z']
    columns = []
    for i in range(how_many):
        columns.append(template[0]+str(i+1)) #new x
        columns.append(template[1]+str(i+1)) #new y
        columns.append(template[2]+str(i+1)) #new z
    return columns

def organize_landmarks(landmarks, individual):
   coords = [individual]
   coords.extend(landmarks[['x','y','z']][landmarks['individual']==str(individual)].values.flatten().tolist())
   return [coords]

### Processing fcsv files (markups from 3dSlicer)

def process_fcsv_files(base_path, fnames, out_name, sep):
    data = None
    for fname in fnames:
        if '.fcsv' in fname:
            df = pd.read_csv(base_path+sep+fname, skiprows=2) #skipping header on the fcsv files.
            df = df[df.columns[[1, 2, 3, -3, -1]]] #cleaning and renaming columns
            df.columns = ["x", "y", "z", "label", "individual"]
            individuals = [i[-1] for i in df['individual']]
            df['individual'] = individuals
            df = df[df.columns[[-1, 0, 1, 2, 3]]] #reordering columns
            unique_individuals = df['individual'].unique()
            landmarks_per_individual = get_landmarks_per_individual(df, unique_individuals) #how many landmarks there are per individual.
            new_columns = ['individual']
            new_columns.extend(create_columns(max(landmarks_per_individual)))
            landmarks = []
            for u in unique_individuals:
                landmarks.extend(organize_landmarks(df, u))

            if data is None:
                data = pd.DataFrame(data=landmarks, columns=new_columns)
            else:
                data = data.append(pd.DataFrame(data=landmarks, columns=new_columns))
    
    if data is None:
        print('There is not .fcsv files on {}. Please, use a valid directory.'.format(base_path))
    else:        
        data.to_csv(base_path+sep+out_name, index=None)
        print('Data saved succesfully on {}'.format(base_path+sep+out_name))
        #return data

### Processing .pts files (raw from Landmark)

def process_pts_files(base_path, fnames, out_name, sep):
    data = None
    for fname in fnames:
        if '.pts' in fname:
            #preprocessing
            individual = fname.split('.pts')[0].split('/')[-1] #getting individual's name
            df = pd.read_csv(base_path+sep+fname, skiprows=1, delim_whitespace=True).reset_index() #reads pts file
            col_names = df.columns
            df = df.rename(index=str, columns={col_names[0]:"landmark_id", col_names[1]: "x", col_names[2]: "y", col_names[3]: "z"}) #renaming the columns
            col_ind = [individual for _ in range(df.shape[0])] # creating a column filled with the individual's name
            df = df.assign(individual=pd.Series(col_ind).values) # adding that column to the end
            new_order = [-1, 0, 1, 2, 3]
            df = df[df.columns[new_order]] # reordering columns to get the name one at first.

            #Giving data its final format
            new_columns = ['individual']
            new_columns.extend(create_columns(df.shape[0]))
            landmarks = organize_landmarks(df, individual)
            if data is None:
                data = pd.DataFrame(data=landmarks, columns=new_columns)
            else:
                data = data.append(pd.DataFrame(data=landmarks, columns=new_columns))
    
    if data is None:
        print('There is not .pts files on \'{}\'. Please, use a valid directory.'.format(base_path))
    else:        
        data.to_csv(base_path+sep+out_name, index=None)
        print('Data saved succesfully on \'{}\''.format(base_path+sep+out_name))
        return data



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=str, help="Data directory.")
    parser.add_argument("--mode", help="[fcsv | pts]. Indicates if the script will process .fcsv files or .pts files.", default='fcsv')
    parser.add_argument("-o", "--output-file-name", help="Output file name", default='output.csv')
    args = parser.parse_args()
    base_path = args.directory
    out_name = args.output_file_name
    fnames = []
    if os.path.exists(base_path):
        fnames = os.listdir(base_path)
        fnames.sort()
    else:
        print("Empty directory")

    sep = '\\' if platform.system == 'Windows' else '/'
    if args.mode == 'fcsv' and len(fnames) > 0:
        #print("processing fcsv files in {}".format(base_path))
        process_fcsv_files(base_path, fnames, out_name, sep)
    elif args.mode == 'pts' and len(fnames) > 0:
        #print("processing pts files in {}".format(base_path))
        process_pts_files(base_path, fnames, out_name, sep)
    elif args.mode != 'fcsv' and args.mode != 'pts':
        print("Unknown mode. Try with \'fcsv\' or \'pts\'.")
                