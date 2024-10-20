pub mod grabber;

pub struct GrabbedResult {
    pub status_code: u16,
    pub url: String,
    pub contents: String,
    pub secondary_results: Vec<GrabbedResult>,
}
