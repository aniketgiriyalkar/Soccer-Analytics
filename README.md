# Soccer Analytics - Capstone Project

Aniket Giriyalkar (aag5405@rit.edu)

## Content
open-data : Data Source<br />
2018WC-xGModel-Create a preprocessed Pickle file.ipynb<br />
2018WC-xGModel-Data Exploration.ipynb<br />
2018WC-xGModel-Model Selection.ipynb<br />
2018WC-xGModel-Model Application.ipynb<br />
Best Players for each position-avg of top10 features for that position.ipynb<br />
Best Players for each position-weighted average.ipynb<br />
WC2018-Player Comparision Visualizations.ipynb<br />
xGModel-version1.ipynb <br />


## How to Run
Make of local copy of the folder open-data and set the file path and event path appropriately.<br />
Once that is done simply running each of the .ipynb files should be enough. As of now, these files consist of the latest results. <br />

## How to Use

- For comparision of Best XI and World Cup XI:
<br />To observe the results for my Best XI and to view the code  for how I evaluated my best XI, open the file Best Players for each position-avg of top10 features for that position.ipynb. This was a more fair way to evaluate than using weighted average method for each position.
<br /> The implementation of weighted average method can be observed in the file Best Players for each position-weighted average.ipynb.
<br /> Next, for player comparision the notebook, WC2018-Player Comparision Visualizations.ipynb was used. This consists of the visuals that were attached to the report and the poster. Other player analysis plots were not attractive visually and those cells have been omitted from the notebook.
- For the xG Model:
<br /> 2018WC-xGModel-Create a preprocessed Pickle file.ipynb contains the code for data extraction and cleaning and then converting the clean data frame to a pickle file
<br /> 2018WC-xGModel-Data Exploration.ipynb contains the code used for exploring the dataset.
<br /> 2018WC-xGModel-Model Selection.ipynb consists of the code to  select the features and create models using those feature. It also compares the results of different models and determines the best one.
<br /> 2018WC-xGModel-Model Application includes the code for exploring various applications of the best model.
- For the model that predicts the numeber of goals:
<br /> xGModel-version1.ipynb consists the code for Decision Tree Classifier model, that predicts the number of goals scored in the dataset using the xG factor associated with the shot.






