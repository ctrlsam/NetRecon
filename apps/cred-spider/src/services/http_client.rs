use lazy_static::lazy_static;
use std::error::Error;
use std::time::Duration;

lazy_static! {
    static ref HTTP_CLIENT: reqwest::Client = reqwest::Client::builder()
        .timeout(Duration::from_secs(10))
        .danger_accept_invalid_certs(true)
        .user_agent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        .no_gzip()
        .no_deflate()
        .no_brotli()
        .build()
        .unwrap();
}

pub struct ServerResponse {
    pub response_code: u16,
    pub html_content: String,
}

pub async fn get_request(url: &str) -> Result<ServerResponse, Box<dyn Error>> {
    let res = match HTTP_CLIENT
        .get(url)
        .send()
        .await {
            Ok(response) => response,
            Err(err) => return Err(Box::new(err)),
        };

    Ok(ServerResponse {
        response_code: res.status().as_u16(),
        html_content: res.text().await?,
    })
}
