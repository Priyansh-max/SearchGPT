import React, { useState } from 'react';

/** Build equivalent HTTP-request snippets for /api/v1/query in many languages. */
export const buildQuerySnippets = ({ base = '{BASE_URL}', apiKey = '<your key>' } = {}) => {
  const url = `${base}/api/v1/query`;
  const compact = `{"mode":"search","query":"best laptops 2026","options":{"synthesize":true}}`;
  return [
    { label: 'cURL', code:
`curl -X POST ${url} \\
  -H "X-API-Key: ${apiKey}" \\
  -H "Content-Type: application/json" \\
  -d '${compact}'` },
    { label: 'Python', code:
`import requests

resp = requests.post(
    "${url}",
    headers={"X-API-Key": "${apiKey}"},
    json={"mode": "search", "query": "best laptops 2026", "options": {"synthesize": True}},
)
print(resp.json())` },
    { label: 'JavaScript', code:
`const resp = await fetch("${url}", {
  method: "POST",
  headers: {
    "X-API-Key": "${apiKey}",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    mode: "search",
    query: "best laptops 2026",
    options: { synthesize: true },
  }),
});
console.log(await resp.json());` },
    { label: 'Go', code:
`package main

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
)

func main() {
	body := []byte(\`${compact}\`)
	req, _ := http.NewRequest("POST", "${url}", bytes.NewBuffer(body))
	req.Header.Set("X-API-Key", "${apiKey}")
	req.Header.Set("Content-Type", "application/json")
	resp, _ := http.DefaultClient.Do(req)
	defer resp.Body.Close()
	out, _ := io.ReadAll(resp.Body)
	fmt.Println(string(out))
}` },
    { label: 'PHP', code:
`<?php
$ch = curl_init("${url}");
curl_setopt_array($ch, [
  CURLOPT_POST => true,
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_HTTPHEADER => ["X-API-Key: ${apiKey}", "Content-Type: application/json"],
  CURLOPT_POSTFIELDS => json_encode([
    "mode" => "search",
    "query" => "best laptops 2026",
    "options" => ["synthesize" => true],
  ]),
]);
echo curl_exec($ch);` },
    { label: 'Ruby', code:
`require "net/http"
require "json"
require "uri"

uri = URI("${url}")
req = Net::HTTP::Post.new(uri, "X-API-Key" => "${apiKey}", "Content-Type" => "application/json")
req.body = { mode: "search", query: "best laptops 2026", options: { synthesize: true } }.to_json
res = Net::HTTP.start(uri.hostname, uri.port, use_ssl: uri.scheme == "https") { |http| http.request(req) }
puts res.body` },
  ];
};

const CodeTabs = ({ tabs }) => {
  const [active, setActive] = useState(0);
  const [copied, setCopied] = useState(false);
  const current = tabs[active] || tabs[0];

  const copy = async () => {
    try { await navigator.clipboard.writeText(current.code); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch {}
  };

  return (
    <div className="rounded-lg border border-gray-200 dark:border-neutral-800 overflow-hidden">
      <div className="flex items-center justify-between bg-neutral-50 dark:bg-neutral-900 border-b border-gray-200 dark:border-neutral-800">
        <div className="flex overflow-x-auto hide-scrollbar">
          {tabs.map((t, i) => (
            <button key={t.label} onClick={() => setActive(i)}
              className={`px-3 py-2 text-xs whitespace-nowrap border-b-2 -mb-px transition-colors ${
                i === active ? 'border-blue-500 text-black dark:text-white' : 'border-transparent text-gray-500 dark:text-neutral-400 hover:text-black dark:hover:text-white'}`}>
              {t.label}
            </button>
          ))}
        </div>
        <button onClick={copy} className="px-3 py-2 text-xs text-gray-500 dark:text-neutral-400 hover:text-black dark:hover:text-white shrink-0">
          {copied ? 'Copied ✓' : 'Copy'}
        </button>
      </div>
      <pre className="text-xs bg-neutral-100 dark:bg-neutral-950 p-3 overflow-x-auto text-gray-800 dark:text-neutral-200 whitespace-pre">{current.code}</pre>
    </div>
  );
};

export default CodeTabs;
