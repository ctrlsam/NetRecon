use futures::TryStreamExt;
use mongodb::{Client, options::ClientOptions, bson::{doc}};
use chrono::{Utc, Duration};
use serde::{Deserialize, Serialize};

use crate::evaluator::{Confidence, EvaluatedResult};

#[derive(Debug, Serialize, Deserialize)]
pub struct ScanDocument {
    #[serde(rename = "_id", skip_serializing_if = "Option::is_none")]
    pub id: Option<mongodb::bson::oid::ObjectId>,
    pub saddr: String,
    pub sport: i32,
    pub data: Option<ScanData>,
    pub apps: Option<AppData>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AppData {
    pub credspider: Option<CredSpiderData>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CredSpiderData {
    pub last_scan: Option<bson::DateTime>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ScanData {
    pub http: Option<HttpData>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HttpData {
    pub status: String,
    pub protocol: String,
    pub result: HttpResult,
    pub timestamp: bson::DateTime,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HttpResult {
    pub response: Option<HttpResponse>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HttpResponse {
    pub status_line: String,
    pub status_code: i32,
    pub protocol: HttpProtocol,
    #[serde(flatten)]
    pub headers: Option<std::collections::HashMap<String, Vec<String>>>,
    pub body: Option<String>,
    pub body_sha256: Option<String>,
    pub content_length: Option<i32>,
    pub request: HttpRequest,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HttpProtocol {
    pub name: String,
    pub major: Option<i32>,
    pub minor: Option<i32>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HttpRequest {
    pub url: HttpUrl,
    pub method: String,
    #[serde(flatten)]
    pub headers: Option<std::collections::HashMap<String, Vec<String>>>,
    pub host: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HttpUrl {
    pub scheme: String,
    pub host: String,
    pub path: String,
}
pub struct DatabaseService {
    client: Client,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Credential {
    pub name: String,
    pub value: Option<String>,
    pub saddr: String,
    pub sport: i32,
    pub url: String,
    pub confidence: Confidence,
}


impl DatabaseService {
    pub async fn new() -> Result<Self, mongodb::error::Error> {
        let client_options = ClientOptions::parse("mongodb://localhost:27017").await?;
        let client = Client::with_options(client_options)?;
        Ok(Self { client })
    }

    pub async fn get_documents_to_scan(&self, interval: Duration) -> Result<Vec<ScanDocument>, mongodb::error::Error> {
        let database = self.client.database("zmap_results");
        let collection = database.collection::<ScanDocument>("scans");

        let now = Utc::now();
        let threshold = now - interval;
        let filter = doc! {
            //"data.http.result.response.body": { "$exists": true },
            "$or": [
                { "apps.credspider.last_scan": { "$exists": false } },
                { "apps.credspider.last_scan": { "$lt": threshold } }
            ]
        };

        let mut cursor = collection.find(filter, None).await?;
        let mut documents = Vec::new();

        while let Some(doc) = cursor.try_next().await? {
            documents.push(doc);
        }

        Ok(documents)
    }

    pub async fn update_last_scan(&self, ip: &str) -> Result<(), mongodb::error::Error> {
        let database = self.client.database("zmap_results");
        let collection = database.collection::<ScanDocument>("scans");

        let filter = doc! { "ip": ip };
        let update = doc! { 
            "$set": { 
                "apps.credspider.last_scan": bson::DateTime::now() 
            } 
        };

        collection.update_one(filter, update, None).await?;

        Ok(())
    }

    pub async fn insert_credentials(&self, ip: &str, port: i32, credentials: Vec<(String, EvaluatedResult)>) -> Result<(), mongodb::error::Error> {
        let database = self.client.database("zmap_results");
        let collection = database.collection::<Credential>("credentials");
    
        for (_, result) in credentials {
            for secret in result.keys {
                // Convert Result<String, ()> to Option<String> for MongoDB insertion
                let value = match secret.value {
                    Ok(ref val) => Some(val.clone()),
                    Err(_) => None,
                };
    
                // Create a document to insert
                let document = Credential {
                    name: secret.name,
                    value,
                    saddr: ip.to_string(),
                    sport: port,
                    url: secret.source,
                    confidence: secret.confidence,
                };
    
                // Upsert the document into MongoDB by saddr, sport, and name fields
                let filter = doc! {
                    "saddr": &document.saddr,
                    "sport": document.sport,
                    "name": &document.name,
                    "url": &document.url,
                };
                let update = doc! {
                    "$set": {
                        "value": &document.value,
                        "confidence": bson::to_bson(&document.confidence)?,
                    }
                };
                collection.update_one(filter, update, mongodb::options::UpdateOptions::builder().upsert(true).build()).await?;
            }
        }
    
        Ok(())
    }
}