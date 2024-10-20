use crate::evaluator::Confidence;

use super::{Finder, Secret};
use regex::Regex;

pub struct RegexFinder {
    pub name: String,
    pub regex: Regex,
    pub confidence: Confidence,
}

impl RegexFinder {
    pub fn new(name: &str, regex: &Regex, confidence: Confidence) -> Self {
        RegexFinder {
            name: name.to_string(),
            regex: regex.to_owned(),
            confidence,
        }
    }
}

impl Finder for RegexFinder {
    fn find(&self, source: &str, content: &str) -> Vec<Secret> {
        self.regex
            .find_iter(content)
            .filter_map(|m| {
                Some(Secret {
                    name: self.name.clone(),
                    value: Ok(m.as_str().to_string()),
                    source: source.to_string(),
                    confidence: self.confidence,
                })
            })
            .collect()
    }
}
