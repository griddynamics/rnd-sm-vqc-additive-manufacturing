# Requirements 


To install BlenderAPI 
Download BPY wheel at https://pypi.org/project/bpy/#files for Python3.10 and add 
local URL to requirements.txt

To install conda environment run
```
conda env create -f environment.yml
```
# Data generation

The data generation config file can be found in src/config/main_config.yaml
Configure desired parameters
To run the data generation script run the following commands
```
conda activate ma-vqc-data-preprocessing
python src/run.py
```

2 datasets need to be generated. Be sure to change the save path when generating and changing random seed so
as not to save over previously generated files and to avoid duplicate generation.
1 for random forest propensity model and another one for PointNet and RandomForest classifier training.

# Data preprocessing and model trainig

Inside the notebooks folder you can find the relevant preprocessing and training steps

## Contents:

RandomForest.ipynb is used for Random Forest propensity and classifier model as well as 
per point aggregation function scripts used for Random Forest classifier model

PointNet.ipynb is used to train PointNet using iterative farthest point downsampling as well
as Random Forest sampling techniques. Random Forest sampled dataset is saved for use in
the following 2 notebooks.

PointNet(IFP)+RandomForest.ipynb notebook extracts the xb1 and xb2 embedding layers of 512 and 256 dimensions
respectively and concatenates the vectors to the aggregated data to be used for Random Forest classifier.

PointNet(RF)+RandomForest.ipynb uses the same principle but uses Random Forest sampling as the input data
to get the PointNet predictions.

The notebooks should be run in the order they were metionned in.

notebooks/model_weights folder will contain all model embeddings
notebooks/data folder contains all data including point dataset, selected samples for Random Forest propensity model,
mesh training dataset, aggregated datasets and RandomForest sampled datasets

## License
```
Copyright 2022 Grid Dynamics International, Inc. All Rights Reserved

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
