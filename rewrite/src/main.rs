use chrono::{DateTime, Utc};
use futures::stream::{self, StreamExt};
use reqwest::Client;
use scraper::{Html, Selector};
use serde::{Deserialize, Serialize};
use std::collections::{HashSet, VecDeque};
use std::fs::{File, OpenOptions};
use std::io::{Read, Write, Seek, SeekFrom};
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Mutex;
use tokio::time::sleep;
use url::Url;

#[derive(Debug, Serialize, Deserialize, Clone)]
struct UrlData {
    url: String,
    title: String,
    found_at: String,
    timestamp: DateTime<Utc>,
    status_code: u16,
}

struct UrlFinder {
    base_url: String,
    domain: String,
    max_pages: usize,
    same_domain_only: bool,
    visited_urls: HashSet<String>,
    found_urls: Vec<UrlData>,
    client: Client,
}

impl UrlFinder {
    fn new(base_url: &str, max_pages: usize, same_domain_only: bool) -> Self {
        let parsed_url = Url::parse(base_url).expect("Invalid base URL");
        let domain = parsed_url.host_str().unwrap_or("").to_string();
        
        let client = Client::builder()
            .timeout(Duration::from_secs(10))
            .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            .build()
            .expect("Failed to create HTTP client");

        UrlFinder {
            base_url: base_url.to_string(),
            domain,
            max_pages,
            same_domain_only,
            visited_urls: HashSet::new(),
            found_urls: Vec::new(),
            client,
        }
    }

    fn is_valid_url(&self, url: &str) -> bool {
        if url.is_empty() 
            || url.starts_with('#')
            || url.starts_with("javascript:")
            || url.starts_with("mailto:")
            || url.starts_with("tel:") {
            return false;
        }

        if let Ok(parsed_url) = Url::parse(url) {
            if self.same_domain_only {
                return parsed_url.host_str().unwrap_or("") == self.domain;
            }
            return true;
        }
        false
    }

    async fn process_url(&self, url: &str, found_at: &str) -> Result<(UrlData, Vec<String>), Box<dyn std::error::Error>> {
        let response = self.client.get(url).send().await?;
        let status_code = response.status().as_u16();
        let text = response.text().await?;

        let document = Html::parse_document(&text);
        let title_selector = Selector::parse("title").unwrap();
        let title = document
            .select(&title_selector)
            .next()
            .and_then(|t| Some(t.inner_html()))
            .unwrap_or_else(|| url.to_string());

        let url_data = UrlData {
            url: url.to_string(),
            title: title.trim().to_string(),
            found_at: found_at.to_string(),
            timestamp: Utc::now(),
            status_code,
        };

        let link_selector = Selector::parse("a[href]").unwrap();
        let base_url = Url::parse(url)?;
        let mut new_urls = Vec::new();

        for link in document.select(&link_selector) {
            if let Some(href) = link.value().attr("href") {
                if let Ok(absolute_url) = base_url.join(href) {
                    let absolute_url_str = absolute_url.as_str().to_string();
                    if self.is_valid_url(&absolute_url_str) {
                        new_urls.push(absolute_url_str);
                    }
                }
            }
        }

        Ok((url_data, new_urls))
    }

    async fn find_urls(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let mut queue = VecDeque::new();
        queue.push_back(("starting_point".to_string(), self.base_url.clone()));
        
        while let Some((found_at, url)) = queue.pop_front() {
            if self.visited_urls.len() >= self.max_pages {
                break;
            }

            if !self.visited_urls.contains(&url) {
                self.visited_urls.insert(url.clone());
                
                match self.process_url(&url, &found_at).await {
                    Ok((url_data, new_urls)) => {
                        self.found_urls.push(url_data);
                        
                        for new_url in new_urls {
                            if !self.visited_urls.contains(&new_url) {
                                queue.push_back((url.clone(), new_url));
                            }
                        }
                        
                        sleep(Duration::from_millis(100)).await;
                    }
                    Err(e) => {
                        eprintln!("Error processing {}: {}", url, e);
                    }
                }
            }
        }
        
        Ok(())
    }

    fn save_results(&self, filename: &str) -> std::io::Result<()> {
        let mut existing_data = Vec::new();
        if let Ok(mut file) = File::open(filename) {
            file.read_to_end(&mut existing_data)?;
        }

        let mut all_urls = Vec::new();
        
        if !existing_data.is_empty() {
            if let Ok(mut existing_urls) = serde_json::from_slice::<Vec<UrlData>>(&existing_data) {
                all_urls.append(&mut existing_urls);
            }
        }

        all_urls.extend(self.found_urls.clone());

        all_urls.sort_by(|a, b| a.url.cmp(&b.url));
        all_urls.dedup_by(|a, b| a.url == b.url);

        let json = serde_json::to_string_pretty(&all_urls)?;
        let mut file = File::create(filename)?;
        file.write_all(json.as_bytes())?;
        println!("Results saved to {} (total entries: {})", filename, all_urls.len());
        Ok(())
    }

    fn export_urls_to_txt(&self, filename: &str) -> std::io::Result<()> {
        let mut existing_urls = HashSet::new();
        if let Ok(mut file) = File::open(filename) {
            let mut content = String::new();
            file.read_to_string(&mut content)?;
            
            existing_urls.extend(
                content
                    .split(',')
                    .filter(|s| !s.is_empty())
                    .map(|s| s.trim().trim_matches('"').to_string())
            );
        }

        for data in &self.found_urls {
            existing_urls.insert(data.url.clone());
        }

        let mut all_urls: Vec<_> = existing_urls.into_iter().collect();
        all_urls.sort();

        let urls_text = all_urls
            .iter()
            .map(|url| format!("\"{}\"", url))
            .collect::<Vec<_>>()
            .join(",");

        let mut file = File::create(filename)?;
        file.write_all(urls_text.as_bytes())?;
        println!("URLs exported to {} (total entries: {})", filename, all_urls.len());
        Ok(())
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let urls = vec![
        "https://www.w3schools.com/js/",
        "https://www.typescriptlang.org/docs/",
        "https://www.w3schools.com/html",
        "https://www.w3schools.com/css",
        "https://www.w3schools.com/sql",
        "https://www.w3schools.com/typescript",
        "https://tailwindcss.com/docs",
        "https://svelte.dev/docs/cli/",
        "https://svelte.dev/docs/kit/",
        "https://svelte.dev/docs/svelte"
    ];

    for url in urls {
        let mut finder = UrlFinder::new(
            url,
            100,  // max_pages
            true  // same_domain_only
        );

        println!("\nStarting URL finder for {}", url);
        println!("Max pages: {}", finder.max_pages);
        println!("Same domain only: {}", finder.same_domain_only);

        finder.find_urls().await?;
        
        println!("Found {} new URLs", finder.found_urls.len());

        finder.save_results("../svelte/urls.json")?;
        finder.export_urls_to_txt("../svelte/urls.txt")?;

        let domains: HashSet<_> = finder.found_urls
            .iter()
            .filter_map(|url_data| Url::parse(&url_data.url).ok())
            .filter_map(|url| url.host_str().map(|s| s.to_string()))
            .collect();

        println!("Unique domains found in this batch: {}", domains.len());
        println!("Sample of newly found URLs:");
        for url_data in finder.found_urls.iter().take(5) {
            println!("- {} (found at: {})", url_data.url, url_data.found_at);
        }
    }

    Ok(())
}