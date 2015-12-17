/**
* Copyright 2012-2013 The MITRE Corporation.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 *
 *
 * **************************************************************************
 * NOTICE This software was produced for the U. S. Government under Contract No.
 * W15P7T-12-C-F600, and is subject to the Rights in Noncommercial Computer
 * Software and Noncommercial Computer Software Documentation Clause
 * 252.227-7014 (JUN 1995)
 *
 * (c) 2012 The MITRE Corporation. All Rights Reserved.
 * **************************************************************************
 *
 */
package org.opensextant.output;


import java.util.HashMap;
import java.util.Map;

import org.opensextant.processing.ProcessingException;

/**
 *
 * @author Marc C. Ubaldino, MITRE, ubaldino at mitre dot org
 */
public class FormatterFactory {

    /**
     *
     */
    private static final String[] OUTPUT_FORMATS = {"CSV", "GeoCSV", "FileGDB", "GDB", "JSON", "KML", "WKT", "Shapefile", "SHP"};
    private static final Map<String,String> OUTPUT_FORMATS_LOOKUP = new HashMap<String,String>();

    static {
        for (String fmt : OUTPUT_FORMATS) {
            OUTPUT_FORMATS_LOOKUP.put(fmt.toLowerCase(), fmt);
        }
        OUTPUT_FORMATS_LOOKUP.put("shp", "Shapefile");
        OUTPUT_FORMATS_LOOKUP.put("filegdb", "GDB");

    }

    /**
     * Check if this is a known format
     */
    public static boolean isSupported(String fmt) {
        if (fmt==null){
            return false;
        }
        return OUTPUT_FORMATS_LOOKUP.containsKey(fmt.toLowerCase());
    }

    public static String[] getSupportedFormats() {
        return OUTPUT_FORMATS;
    }
    /**
     *
     */
    public static String PKG = FormatterFactory.class.getPackage().getName();

    /**
     * Supported formats are CSV, WKT, HTML, KML, Shapefile, GDB, JSON
     *
     * @param fmt
     * @return
     * @throws ProcessingException
     */
    public static ResultsFormatter getInstance(String fmt) throws ProcessingException {

        String formatterClass = OUTPUT_FORMATS_LOOKUP.get(fmt.toLowerCase());
        if (formatterClass==null){
            throw new ProcessingException("Unsupported Formatter: " + fmt);
        }

        formatterClass = PKG + "." + formatterClass + "Formatter";

        try {
            return (ResultsFormatter) (Class.forName(formatterClass)).newInstance();
        } catch (ClassNotFoundException e) {
            throw new ProcessingException("Formatter not found for " + fmt, e);
        } catch (InstantiationException e) {
            throw new ProcessingException("Formatter could not start for " + fmt, e);
        } catch (IllegalAccessException e) {
            throw new ProcessingException("Formatter could not start for " + fmt, e);
        }
    }
}
