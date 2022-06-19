# DeKnow Identity Service

Service that helps obtain data from Scholar. The service can be accessed at . Supports
* Profiles - https://scholar.google.com/citations?user=H9sNlFYAAAAJ&hl=en&oi=sra
* Articles - https://scholar.google.com/citations?view_op=view_citation&hl=en&user=H9sNlFYAAAAJ&citation_for_view=H9sNlFYAAAAJ:b0M2c_1WBrUC

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Installing

Install the packages required.

```
apt-get install python3
pip install requirements.txt
```

## Deployment

### Initialize the database

Initialize the database using the command.

```
flask init-db
```

### Deploy the service

```
flask run
flask run -h localhost -p 4000
```

Database and logs can be obtained from the ```/instance``` folder.
