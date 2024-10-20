use crate::services::http_client::get_request;
use async_recursion::async_recursion;
use reqwest::Url;
use scraper::{Html, Selector};
use std::{collections::HashSet, error::Error};

use super::GrabbedResult;

use regex::Regex;
use std::sync::Arc;

pub struct GrabberConfig {
    pub url_filters: Arc<Vec<Regex>>,
}

#[async_recursion()]
pub async fn grab(
    url: &str,
    secondary: &bool,
    config: &GrabberConfig,
) -> Result<GrabbedResult, Box<dyn Error>> {
    let response = match get_request(url).await {
        Ok(res) => res,
        Err(err) => return Err(err),
    };

    let links = get_script_urls(&url, &response.html_content, &config.url_filters);
    let mut secondary_results: Vec<GrabbedResult> = Vec::new();

    if *secondary {
        for link in links {
            let result = grab(&link, &false, config).await?;
            secondary_results.push(result);
        }
    }

    Ok(GrabbedResult {
        status_code: response.response_code,
        url: url.to_string(),
        contents: response.html_content,
        secondary_results,
    })
}

pub fn get_script_urls(
    base_url: &str,
    html_content: &str,
    url_filters: &Arc<Vec<Regex>>,
) -> Vec<String> {
    let document = Html::parse_document(html_content);
    let mut links = Vec::new();
    let mut seen = HashSet::new();

    let base = Url::parse(base_url).expect("Failed to parse base URL");

    let script_selector = Selector::parse("script[src]").unwrap();

    for element in document.select(&script_selector) {
        if let Some(href) = element.value().attr("src") {
            if url_filters.iter().any(|regex| regex.is_match(href)) {
                continue; // Skip URLs matching any of the provided regex patterns
            }

            match base.join(href) {
                Ok(absolute_url) => {
                    if seen.insert(absolute_url.to_string()) {
                        links.push(absolute_url.to_string());
                    }
                }
                Err(e) => println!("Error resolving URL: {}", e),
            }
        }
    }

    links
}
