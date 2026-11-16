Employee Data Analyzer

A Python program that reads an employee CSV file, cleans the data, and produces summaries, comparison tables and charts. It helps answer practical HR questions: who the employees are, where they work, how much experience they have, and which groups are more likely to leave.

Author: Aayush Tiwari
ERP No: RU-26-00375
Institution: Rungta International Skills University (B.Tech 1st Sem, IBM)

Features
Data cleaning
Trims extra spaces in text fields (" Pune " and "Pune" are treated the same)
Removes duplicate rows
Fills missing numeric values with the median and missing text values with the most common value
Console summary
Missing-value check and numeric summary
Average age and average experience in the current domain
Employee counts by city and by education
Number of employees who stayed vs. left, and the leaving percentage
Comparison tables (saved as text/CSV files)
Every pair of categorical columns, with counts and row percentages
Every numeric column grouped by every category (count, mean, median, min, max)
Numeric summary and correlation matrix
Charts (saved as PNG images)
Distribution of each categorical column
Box plots comparing numeric columns across categories
Scatter plots for every pair of numeric columns
Correlation heatmap
Leaving rate by category
Stayed vs. left bar chart
Dataset

The program expects a file named Employee.csv with these columns:

Column	Type	Description
Education	Text	Education level
JoiningYear	Number	Year the employee joined
City	Text	City of work
PaymentTier	Number	Payment tier
Age	Number	Age of the employee
Gender	Text	Gender
EverBenched	Text	Whether the employee was ever benched
ExperienceInCurrentDomain	Number	Years of experience in the current domain
LeaveOrNot	Number (0/1)	1 if the employee left, 0 if the employee stayed

The dataset is not included in this repository. Place your own Employee.csv in the project folder.

Technologies Used
Python 3.8+
Pandas: loading, cleaning and grouping data
NumPy: median and numeric calculations
Matplotlib: charts and saving images
Seaborn: box plots, scatter plots and heatmap
itertools and pathlib (standard library): column pairs and file paths
