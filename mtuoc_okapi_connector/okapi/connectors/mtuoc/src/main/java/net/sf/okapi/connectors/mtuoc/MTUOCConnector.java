/*===========================================================================
  Copyright (C) 2025 by Tommi Nieminen
-----------------------------------------------------------------------------
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
===========================================================================*/

/*Adapted from the ModernMT connector, Copyright (C) 2017 by the Okapi Framework contributors*/

package net.sf.okapi.connectors.mtuoc;

import net.sf.okapi.common.IParameters;
import net.sf.okapi.common.Util;
import net.sf.okapi.common.exceptions.OkapiException;
import net.sf.okapi.common.query.MatchType;
import net.sf.okapi.common.query.QueryResult;
import net.sf.okapi.common.resource.TextFragment;
import net.sf.okapi.lib.translation.BaseConnector;
import net.sf.okapi.lib.translation.QueryUtil;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpRequest.BodyPublishers;
import java.time.Duration;
import java.util.concurrent.ThreadLocalRandom;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

/**
 * Connector for the MTUOC MT Engine API</a>.
 */
public class MTUOCConnector extends BaseConnector {

    private static final String TRANSLATE_METHOD = "/translate";

    private Parameters params;
    private JSONParser parser;
    private QueryUtil util;

    public MTUOCConnector () {
        params = new Parameters();
        util = new QueryUtil();
        parser = new JSONParser();
    }

    @Override
    public String getName () {
        return "MTUOC API Connector";
    }

    @Override
    public String getSettingsDisplay () {
    	return "MTUOC URL: " + params.getUrl();
    }

    @Override
    public void close () {
        // Nothing to do
    }

    @Override
    public void open () {
        // Nothing to do
    }

    @Override
    public int query (String plainText) {
        return query(new TextFragment(plainText));
    }

    /**
     * Queries the MTUOC API from the configured server.
     * @param fragment the fragment to query.
     * @return the number of translations (1 or 0).
     */
    @Override
    public int query (TextFragment fragment) {
        current = -1;
        try {
            if (!fragment.hasText(false)) {
                return 0;
            }
            if (Util.isEmpty(params.getUrl())) {
                throw new OkapiException("You must have a URL configured for your MTUOC Engine.");
            }
            
            StringBuilder sb = new StringBuilder(params.getUrl()).append(TRANSLATE_METHOD);
            String qtext = util.toCodedHTML(fragment);

            String url = sb.toString();

            // Create JSON payload using json-simple
            JSONObject payload = new JSONObject();
            payload.put("src", qtext);
            payload.put("id", ThreadLocalRandom.current().nextInt(1, 1001));
            payload.put("srcLang", srcLoc.getLanguage());
            payload.put("tgtLang", trgLoc.getLanguage());
            payload.put("tgtLang", trgLoc.getLanguage());
            String jsonPayload = payload.toJSONString();

            // Create HTTP client
            HttpClient client = HttpClient.newBuilder()
                    .version(HttpClient.Version.HTTP_1_1)
                    .connectTimeout(Duration.ofSeconds(10))
                    .build();

            // Build request
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .header("Content-Type", "application/json")
                    .POST(BodyPublishers.ofString(jsonPayload))
                    .build();

            // Send request and get response
            HttpResponse<String> response = client.send(
                request, HttpResponse.BodyHandlers.ofString());

            // Check for errors
            if (response.statusCode() >= 400) {
                throw new RuntimeException("HTTP Error " + response.statusCode() + 
                                        ": " + response.body());
            }

            // 4. Parse JSON response
            JSONParser parser = new JSONParser();
            JSONObject object = (JSONObject) parser.parse(response.body());

            String translation = (String) object.get("tgt");

            result = new QueryResult();
            result.weight = getWeight();
            result.source = fragment;
            if (fragment.hasCode()) {
                result.target = new TextFragment(util.fromCodedHTML(translation, fragment, true),
                        fragment.getClonedCodes());
            } else {
                result.target = new TextFragment(util.fromCodedHTML(translation, fragment, true));
            }
            result.setFuzzyScore(95);
            result.origin = getName();
            result.matchType = MatchType.MT;
            current = 0;
        }
        catch (Throwable e) {
            throw new OkapiException("Error querying the server.\n" + e.getMessage(), e);
        }
        return ((current==0) ? 1 : 0);
    }

    @Override
    public Parameters getParameters () {
        return params;
    }

    @Override
    public void setParameters (IParameters params) {
        this.params = (Parameters) params;
    }

}
