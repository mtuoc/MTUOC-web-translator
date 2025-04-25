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

import net.sf.okapi.common.ParametersDescription;
import net.sf.okapi.common.StringParameters;
import net.sf.okapi.common.uidescription.EditorDescription;
import net.sf.okapi.common.uidescription.IEditorDescriptionProvider;
import net.sf.okapi.common.uidescription.TextInputPart;

/**
 * Parameters for the {@link MTUOCConnector}.
 */
public class Parameters extends StringParameters implements IEditorDescriptionProvider {

	private static final String URL = "url";

	public Parameters() {
	}

	public String getUrl () {
		return getString(URL);
	}

	public void setUrl(String url) {
		setString(URL, url);
	}

	@Override
	public void reset () {
		super.reset();
        setUrl("");
	}

	@Override
	public ParametersDescription getParametersDescription () {
		ParametersDescription desc = new ParametersDescription(this);
		desc.add(URL,
			"URL for MTUOC Engine",
			"The MTUOC Engine's API URL - format http://<servername>:<port>");
		return desc;
	}

	@Override
	public EditorDescription createEditorDescription (ParametersDescription paramsDesc) {
		EditorDescription desc = new EditorDescription("MTUOC Engine Connector Settings", true, false);
		desc.addTextInputPart(paramsDesc.get(URL));
		//TextInputPart tip = desc.addTextInputPart(paramsDesc.get(CONTEXT));
		//tip.setAllowEmpty(true);
		return desc;
	}

}
