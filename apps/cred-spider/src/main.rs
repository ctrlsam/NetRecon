use clap::{arg, command, value_parser};
use cred_spider::{
    evaluator::{evaluate::Evaluator, EvaluatedResult},
    grabber::grabber::{self, GrabberConfig},
    helpers::{self, config_parser::Config},
    services::database::{DatabaseService, ScanDocument},
};
use futures::stream::{self, StreamExt};
use indicatif::ProgressBar;
use std::path::PathBuf;
use chrono::Duration;

#[tokio::main]
async fn main() {
    let matches = command!()
        .name("CredSpider")
        .version("1.0")
        .about("Searches for secret treasure hidden in websites")
        .arg(
            arg!(-c --config <FILE> "Sets a custom file for config")
                .required(false)
                .value_parser(value_parser!(PathBuf))
                .default_value("config/default.yml"),
        )
        .arg(
            arg!(-i --interval <HOURS> "Sets the interval in hours before rescanning")
                .required(false)
                .value_parser(value_parser!(u64))
                .default_value("24"),
        )
        .get_matches();

    let config_file_path = matches.get_one::<PathBuf>("config").unwrap();
    let config: Config =
        helpers::config_parser::load_config_from_yaml(config_file_path.to_str().unwrap())
            .unwrap_or_else(|e| {
                eprintln!("Failed to load config from YAML: {}", e);
                std::process::exit(1);
            });

    let evaluator = Evaluator::new(helpers::config_parser::create_regex_finders(
        config.evaluator,
    ));
    let grabber_config = GrabberConfig {
        url_filters: helpers::config_parser::convert_ignore_url_regex(config.grabber).into(),
    };

    let interval = Duration::hours(matches.get_one::<u64>("interval").unwrap().to_owned() as i64);

    let db_service = DatabaseService::new().await.unwrap_or_else(|e| {
        eprintln!("Failed to connect to database: {}", e);
        std::process::exit(1);
    });

    process_documents(&db_service, interval, &evaluator, &grabber_config).await;
}

async fn handle_document(
    document: &ScanDocument,
    evaluator: &Evaluator,
    grabber_config: &GrabberConfig,
) -> Result<Vec<(String, EvaluatedResult)>, String> {
    let ip = &document.saddr;
    let port = document.sport;

    // Check if the response body exists in the document
    let body = document.data.as_ref()
        .and_then(|data| data.http.as_ref())
        .and_then(|http| http.result.response.as_ref())
        .and_then(|response| response.body.as_deref().map(|s| s.to_string()));

    // If body doesn't exist, query the ip:port
    let (url, body): (String, String) = if let Some(body) = body {
        // Construct URL from existing data if available
        let url = document.data.as_ref()
            .and_then(|data| data.http.as_ref())
            .and_then(|http| http.result.response.as_ref())
            .map(|response| format!(
                "{}://{}{}",
                response.request.url.scheme,
                response.request.url.host,
                response.request.url.path
            ))
            .unwrap_or_else(|| format!("http://{}:{}", ip, port));
        (url, body)
    } else {
        // Query the ip:port
        let url = format!("http://{}:{}", ip, port);
        match grabber::grab(&url, &false, grabber_config).await {
            Ok(grab_result) => (url, grab_result.contents),
            Err(err) => return Err(format!("Error grabbing content from {}: {}", url, err)),
        }
    };

    let mut results = Vec::new();

    // Evaluate main content
    let evaluated_result = evaluator
        .evaluate_content(&url, &body)
        .await
        .map_err(|err| format!("Error evaluating document {}: {}", ip, err))?;
    
    if !evaluated_result.keys.is_empty() {
        results.push((url.clone(), evaluated_result));
    }

    // Resolve and analyze JS links
    let links = grabber::get_script_urls(&url, &body, &grabber_config.url_filters);
    for link in links {
        // println!("Evaluating JS link: {}", link);
        match grabber::grab(&link, &false, grabber_config).await {
            Ok(grab_result) => {
                //println!("Evaluating JS content: {}", grab_result.contents);
                let js_result = evaluator
                    //.evaluate(&grab_result)
                    .evaluate_content(&link, &grab_result.contents)
                    .await
                    .map_err(|err| format!("Error evaluating JS {}: {}", link, err))?;
                if !js_result.keys.is_empty() {
                    results.push((link, js_result));
                }
            }
            Err(_) => (),
        }
    }

    Ok(results)
}

// Update the main function to use the new handle_document return type
async fn process_documents(
    db_service: &DatabaseService,
    interval: Duration,
    evaluator: &Evaluator,
    grabber_config: &GrabberConfig,
) {
    let documents = db_service.get_documents_to_scan(interval).await.unwrap_or_else(|e| {
        eprintln!("Failed to get documents from database: {}", e);
        std::process::exit(1);
    });

    let documents_len = documents.len() as u64;
    let bar = ProgressBar::new(documents_len);
    let documents_stream = stream::iter(documents.into_iter());

    documents_stream
        .for_each_concurrent(Some(200), |document| {
            let bar = bar.clone();
            let db_service = db_service;
            async move {
                match handle_document(&document, evaluator, grabber_config).await {
                    Ok(results) => {
                        if !results.is_empty() {
                            println!("[{}]", document.saddr);
                            for (source, evaluated_result) in &results {
                                println!("{}Source: {}", " ".repeat(4), source);
                                println!("{}Keys:", " ".repeat(4));
                                for key in &evaluated_result.keys {
                                    println!("{}{:#?}", " ".repeat(8), key);
                                }
                            }
                            db_service.insert_credentials(&document.saddr, document.sport, results).await.unwrap_or_else(|e| {
                                eprintln!("Failed to insert credentials for {}: {}", document.saddr, e);
                            });
                        }
                    }
                    Err(_err) => {
                        //println!("Error for IP {}: {}", document.saddr, err);
                    }
                }
                bar.inc(1);
            }
        })
        .await;
}