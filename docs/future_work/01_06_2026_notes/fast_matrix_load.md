# Importing and exporting matrices

Instead of sharing within the application, as this is a tool oriented to teaching, proffesors might want to create their sets of matrices and serve them to theirs students in .json files or in zip files containing several .json file (each .json file is a matrix).

For that reason, we must define an export-import strategy

## Exporting matrices

Matrices will be exported as a `.json` file, containing all the information necessary to recreate the specie and all its information. We can export and import those csvs

Optionally, we can also let the user export the matrix as a `.csv`. The matter with this csv is that, we can export a matrix as a csv but we cannot import it, as we'll lose iformation on the way. The format of the csv will be:

```csv
{stage1};{stage2};{stageN}
{value11};{value12};{value1N}
{value21};{value22};{value2N}
{valueN1};{valueN2};{valueNN}
```

In the `.csv` we will only export the Matrix A


## Importing matrices

The only format valid is a `.json` file following the correct schema. Alternatively, we must let clients also upload a `.zip` file containing several `.json` files. We also must let the users upload more than one `.json` file at the same time in a non-compressed format. In other words, select more tan one file and upload them at the same time. This jsons must contain all the information necessary to create a new specie. At least, Matrix A must be present in the file. If there's no matrix U and F we will create a default version of this matrices by just creating an all zeros matrix with the same dimensions.