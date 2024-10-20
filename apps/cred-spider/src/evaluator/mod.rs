use serde::{Deserialize, Serialize};

pub mod evaluate;
pub mod finders;


#[derive(Debug, Copy, Clone, Serialize, Deserialize)]
pub enum Confidence {
    High,
    Medium,
    Low,
}

#[derive(Debug)]
pub struct Secret {
    pub name: String,
    pub value: Result<String, ()>,
    pub source: String,
    pub confidence: Confidence,
}


pub struct EvaluatedResult {
    pub keys: Vec<Secret>,
}
