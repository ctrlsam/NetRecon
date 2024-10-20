use regex::Regex;
use serde::{Deserialize, Serialize};
use std::fs;

use crate::evaluator::{
    finders::{regex_finder::RegexFinder, Finder},
    Confidence,
};

#[derive(Serialize, Deserialize, Debug)]
pub struct Config {
    pub grabber: Grabber,
    pub evaluator: Evaluator,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Grabber {
    pub ignore_url_regex: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Evaluator {
    pub patterns: Vec<Pattern>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Pattern {
    pub name: String,
    pub regex: String,
    pub confidence: String,
}

pub fn load_config_from_yaml(file_path: &str) -> Result<Config, Box<dyn std::error::Error>> {
    let contents = fs::read_to_string(file_path)?;
    let config: Config = serde_yaml::from_str(&contents)?;
    Ok(config)
}

pub fn create_regex_finders(evaluator: Evaluator) -> Vec<Box<dyn Finder>> {
    evaluator
        .patterns
        .into_iter()
        .map(|pattern| {
            let regex = Regex::new(&pattern.regex).unwrap();
            let confidence = match pattern.confidence.as_str() {
                "high" => Confidence::High,
                "medium" => Confidence::Medium,
                _ => Confidence::Low,
            };
            Box::new(RegexFinder::new(&pattern.name, &regex, confidence)) as Box<dyn Finder>
        })
        .collect()
}

pub fn convert_ignore_url_regex(grabber: Grabber) -> Vec<Regex> {
    grabber
        .ignore_url_regex
        .into_iter()
        .map(|pattern| Regex::new(&pattern).unwrap())
        .collect()
}
