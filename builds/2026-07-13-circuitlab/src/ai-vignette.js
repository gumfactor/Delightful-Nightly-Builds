/* CircuitLab optional AI vignette generation.
   Calls the Anthropic Messages API directly from the browser using a user-supplied,
   session-only API key. This is the ONLY network call in the whole build, and it only
   fires when the user explicitly clicks "Generate New Vignette" with a key entered.
   Tests must intercept/mock this request — never call it live. */

var ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages';
var ANTHROPIC_MODEL = 'claude-haiku-4-5-20251001';

function buildVignetteRequestBody() {
  var regionList = REGION_ORDER.map(function (id) {
    return id + ' (' + REGIONS[id].name + '): ' + REGIONS[id].fn;
  }).join('\n');

  var prompt =
    'You are helping build a neuroscience study aid for a professor who researches empathy, ' +
    'psychopathy, and stress. Write ONE short (2-4 sentence) clinical or research-style vignette ' +
    'describing a symptom, lesion, or experimental finding that clearly implicates exactly one of ' +
    'the following brain regions as the single best answer. Keep it grounded in well-established, ' +
    'general findings — do not invent a fake citation or a fake statistic.\n\n' +
    'Regions:\n' + regionList + '\n\n' +
    'Respond only by calling the submit_vignette tool.';

  return {
    model: ANTHROPIC_MODEL,
    max_tokens: 500,
    tools: [
      {
        name: 'submit_vignette',
        description: 'Submit a generated neuroscience case vignette for the trainer.',
        input_schema: {
          type: 'object',
          properties: {
            text: { type: 'string', description: 'The 2-4 sentence vignette text.' },
            targetRegion: { type: 'string', enum: REGION_ORDER, description: 'The single best-matching region id.' },
            explanation: { type: 'string', description: 'A 1-2 sentence explanation linking the vignette to the target region.' },
          },
          required: ['text', 'targetRegion', 'explanation'],
        },
      },
    ],
    tool_choice: { type: 'tool', name: 'submit_vignette' },
    messages: [{ role: 'user', content: prompt }],
  };
}

function extractToolInput(responseJson) {
  var content = responseJson && responseJson.content;
  if (!Array.isArray(content)) {
    throw new Error('Unexpected response shape from Anthropic API.');
  }
  for (var i = 0; i < content.length; i++) {
    var block = content[i];
    if (block && block.type === 'tool_use' && block.name === 'submit_vignette' && block.input) {
      return block.input;
    }
  }
  throw new Error('AI response did not include a vignette.');
}

async function generateVignette(apiKey) {
  if (!apiKey || typeof apiKey !== 'string' || apiKey.trim().length === 0) {
    throw new Error('An Anthropic API key is required to generate a new vignette.');
  }

  var response;
  try {
    response = await window.fetch(ANTHROPIC_API_URL, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey.trim(),
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify(buildVignetteRequestBody()),
    });
  } catch (networkErr) {
    throw new Error('Could not reach the Anthropic API: ' + networkErr.message);
  }

  var payload;
  try {
    payload = await response.json();
  } catch (parseErr) {
    throw new Error('Anthropic API returned an unreadable response.');
  }

  if (!response.ok) {
    var apiMessage = payload && payload.error && payload.error.message;
    throw new Error(apiMessage || ('Anthropic API request failed (' + response.status + ').'));
  }

  var input = extractToolInput(payload);

  if (!input.targetRegion || !REGIONS[input.targetRegion]) {
    throw new Error('AI returned an unrecognized region.');
  }
  if (!input.text || !input.explanation) {
    throw new Error('AI response was missing required vignette fields.');
  }

  return {
    id: 'ai-' + Date.now(),
    text: input.text,
    targetRegion: input.targetRegion,
    explanation: input.explanation,
    aiGenerated: true,
  };
}
