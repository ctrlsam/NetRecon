use super::{finders::Finder, EvaluatedResult, Secret};

pub struct Evaluator {
    finders: Vec<Box<dyn Finder>>,
}

impl Evaluator {
    pub fn new(finders: Vec<Box<dyn Finder>>) -> Self {
        Self { finders }
    }

    pub fn builder() -> Self {
        Self {
            finders: Vec::new(),
        }
    }

    pub fn with_finder(mut self, finder: Box<dyn Finder>) -> Self {
        self.finders.push(finder);
        self
    }

    pub async fn evaluate_content(
        &self,
        url: &str,
        content: &str,
    ) -> Result<EvaluatedResult, Box<dyn std::error::Error>> {
        let keys = self.get_secrets(url, content);

        Ok(EvaluatedResult {
            keys,
        })
    }

    fn get_secrets(&self, url: &str, contents: &str) -> Vec<Secret> {
        let mut secrets = Vec::new();

        for finder in &self.finders {
            for secret in finder.find(url, contents) {
                secrets.push(secret);
            }
        }

        secrets
    }
}
