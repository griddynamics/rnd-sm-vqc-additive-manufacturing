# Results

### Point dataset 

For Random Forest propensity model the dataset was generated using the following configuration
```
num_of_bisect: 10
num_generations: 10 
```
with same anomaly parameters as the mesh anomaly dataset. Note the seed was changed to give different anomalies
This gives us a dataset size of 200 (100 anomalies vs 100 normal meshes).
20% of the points from this dataset were uniformly sampled.

### Mesh anomaly prediction dataset

For the mesh prediction dataset a total of 4000 meshes were generated. 
Test split was set to 20%.
Same configuration was applied for point model dataset in regards to anomaly size.


#### Default anomaly size

```
sigma_loc: 5
sigma_scale: 5
strength_loc: 5 
strength_scale: 5 
influence_radius_loc: 15 
influence_radius_scale: 10 
```


#### Halved anomaly size

```
sigma_loc: 5
sigma_scale: 5
strength_loc: 2 
strength_scale: 2 
influence_radius_loc: 7 
influence_radius_scale: 5 
```


#### Quartered anomaly size

```
sigma_loc: 5
sigma_scale: 5
strength_loc: 1 
strength_scale: 1 
influence_radius_loc: 3 
influence_radius_scale: 2 
```

### PointNet

For PointNet the following hyperparamters were used.
```
batch_size = 32
sample_rate = 1024
epochs = 10
learning_rate = 0.0001
```
The epochs with best performance were chosen to be used as 
pretrained model in RandomForest+PointNet model. Per epoch performance of model
can be viewed in PointNet metrics excel file.

IFP is a sampling technique used to downsample point clouds to be of the same dimensions. 
IFP (Iterative Farthest point downsampling) selects N points by maximizing the distance between each point
cluster.

RF sampling means the pretrained Random Forest propensity models anomaly probability predictions per point
are used as weights for point selection while downsampling.

### Random Forest + PointNet

For this model the PointNet embeddings were added to the aggregated data of the Random Forest propensity model
to enrich the feature space and train a Random Forest classifier for anomaly predictions.

Full metrics of all best performing models can be viewed in RandomForest+PointNet metrics file.
On the second sheet the metrics for Random Forest propensity model can be viewed
