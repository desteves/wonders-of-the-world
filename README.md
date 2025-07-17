# Wonders of the World: A Vector Search Demo App

Search fun facts about the Wonders of the World based on semantic similarity to a given prompt.

This application demonstrates a vector search functionality using MongoDB Atlas (local and in the cloud) and Sentence Transformers.

## Prereqs

- **Docker**
- **Python 3.11.x**
- **[MongoDB Atlas CLI](https://www.mongodb.com/docs/atlas/cli/current/install-atlas-cli/#install-the-atlas-cli)**
- **[MongoDB Shell](https://www.mongodb.com/docs/mongodb-shell/install/)**

Run `make help` to see all available commands

## Running everything locally (offline)

```sh
# Setup local environment and run application
make setup-local
make run
curl "http://localhost:8080/vectorsearch?prompt=Brazil"
# {
#   "query": "Brazil",
#   "results": [
#     {
#       "_id": "redeemer_13",
#       "score": 0.752901554107666,
#       "text": "Each year, millions of tourists and religious pilgrims visit the statue, making it one of Brazil's most popular attractions."
#     },
#     {
#       "_id": "redeemer_3",
#       "score": 0.739007294178009,
#       "text": "The statue was designed by the Brazilian engineer Heitor da Silva Costa and the French sculptor Paul Landowski."
#     },
#     {
#       "_id": "redeemer_8",
#       "score": 0.7286731004714966,
#       "text": "The statue is illuminated each night, creating a striking view from many locations throughout Rio."
#     },
#     {
#       "_id": "redeemer_1",
#       "score": 0.7215887308120728,
#       "text": "Christ the Redeemer was completed in 1931 and stands on the Corcovado Mountain overlooking Rio de Janeiro."
#     },
#     {
#       "_id": "redeemer_0",
#       "score": 0.7186734676361084,
#       "text": "The Christ the Redeemer statue in Rio de Janeiro stands 30 meters tall (not counting the pedestal) and is made of reinforced concrete and soapstone."
#     }
#   ]
# } 
```

## Running the vector db in the cloud

Launch the application's cloud resources (the vector search database) using Pulumi.

### Prerequisites

1. **[Pulumi CLI](https://www.pulumi.com/docs/get-started/install/)**
     - `PULUMI_ACCESS_TOKEN`:  Your Pulumi Cloud PAT
     - `PULUMI_CONFIG_PASSPHRASE`: To encrypt your Pulumi Stack file
3. **[MongoDB Atlas Environment Variables](https://www.mongodb.com/cloud/atlas/register)**
    - `MONGODB_ATLAS_PROJECT_ID`: The MongoDB Atlas project ID where resources will be created.
    - `MONGODB_ATLAS_PUBLIC_KEY`: The public key for MongoDB Atlas API authentication.
    - `MONGODB_ATLAS_PRIVATE_KEY`: The private key for MongoDB Atlas API authentication.

### Deploy and Run

```sh
# Setup cloud environment (deploys infrastructure and configures app)
make setup-cloud
make run
curl "http://localhost:8080/vectorsearch?prompt=Rome"  
# {
#   "query": "Rome",
#   "results": [
#     {
#       "_id": "colosseum_8",
#       "score": 0.7862097024917603,
#       "text": "It is one of the New Seven Wonders of the World and a symbol of ancient Rome's architectural brilliance."
#     },
#     {
#       "_id": "colosseum_0",
#       "score": 0.7849864959716797,
#       "text": "The Colosseum in Rome, also known as the Flavian Amphitheater, was completed in AD 80 under Emperor Titus."
#     },
#     {
#       "_id": "colosseum_9",
#       "score": 0.7756825685501099,
#       "text": "The Colosseum was built with funds seized from the Roman conquest of Jerusalem."
#     },
#     {
#       "_id": "colosseum_13",
#       "score": 0.7697988152503967,
#       "text": "The Colosseum was partially converted into a Christian site after Rome adopted Christianity as its official religion."
#     },
#     {
#       "_id": "colosseum_10",
#       "score": 0.7597830891609192,
#       "text": "The amphitheater was commissioned by Emperor Vespasian as a gift to the Roman people to boost morale and fortify his political standing."
#     }
#   ]
# }
```

## License

This project is licensed under the MIT License.
