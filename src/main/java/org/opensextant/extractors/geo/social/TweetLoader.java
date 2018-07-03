package org.opensextant.extractors.geo.social;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;

import static org.apache.commons.lang3.StringUtils.isBlank;
import org.opensextant.util.FileUtility;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import jodd.json.JsonObject;
import jodd.json.JsonParser;

public class TweetLoader {
    /**
     * The internals of parsing a JSON file of tweets.
     * 
     * You provide the receiver logic using JSONListener:
     * 
     * <pre>
     *    myListener = JSONListener(){  readObject( String or JSON map); }
     *    
     *    TweetLoader.readJSONByLine(file, myListener)
     *    </pre>
     */

    public static int MAX_ERROR_COUNT = 100;

    /**
     * To read gzip/JSON files one row of JSON at a time.
     * This will tolerate up to MAX_ERROR_COUNT for parsing data files...
     * 
     * @param jsonFile
     * @param ingester
     * @throws IOException
     */
    public static void readJSONByLine(File jsonFile, JSONListener ingester) throws IOException {

        if (!jsonFile.exists()) {
            throw new IOException("File does not exist; not opening...");
        }
        BufferedReader reader = null;
        Logger log = LoggerFactory.getLogger(TweetLoader.class);
        JsonParser jsonp = JsonParser.create();
        int errors = 0;
        try {
            reader = new BufferedReader(FileUtility.getInputStreamReader(jsonFile, "UTF-8"));
            String line;
            while ((line = reader.readLine()) != null) {
                if (isBlank(line)) {
                    // Eat up ^M (\r) or other whitespace.
                    continue;
                }
                /*
                 * control logic. If reader/ingester is done, the close up stream and exit.
                 * 
                 */
                if (ingester.isDone()) {
                    break;
                }

                try {
                    /*
                     * JSON or Text.
                     */
                    if (ingester.preferJSON()) {
                        JsonObject obj = jsonp.parseAsJsonObject(line);
                        ingester.readObject(obj);
                    } else {
                        ingester.readObject(line);
                    }
                } catch (Exception someErr) {
                    ++errors;
                    someErr.printStackTrace();
                    log.error("Ignoring record error ERR={}", someErr.getMessage());
                    log.debug("line failed=" + line, someErr);

                    if (errors > MAX_ERROR_COUNT) {
                        throw new IOException("Exceeded max errors,... Exiting read", someErr);
                    }
                }
            }

        } finally {
            if (reader != null) {
                reader.close();
            }
        }
    }
}
