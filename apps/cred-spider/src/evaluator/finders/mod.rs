use super::Secret;

pub mod regex_finder;

pub trait Finder {
    fn find(&self, source: &str, content: &str) -> Vec<Secret>;
}
