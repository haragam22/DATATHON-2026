/**
 * ResponseText — renders text response_type.
 * Also used as fallback for pipeline errors and unknown types.
 */

import './ResponseRenderers.css';

export default function ResponseText({ envelope, isError = false }) {
  const { data } = envelope;

  // Extract the answer text — try common fields
  let text = '';
  if (typeof data === 'string') {
    text = data;
  } else if (data?.error) {
    text = data.error;
  } else if (data?.clarifying_question) {
    // Abstention — system asks for clarification instead of guessing
    text = data.clarifying_question;
  } else if (data?.answer) {
    text = data.answer;
  } else if (data?.answer_text) {
    text = data.answer_text;
  } else if (data?.text) {
    text = data.text;
  } else if (data?.message) {
    text = data.message;
  } else if (data?.summary) {
    text = data.summary;
  } else {
    // Render raw data as formatted JSON if we can't find text
    const { session_id, ...rest } = data ?? {};
    const keys = Object.keys(rest);
    if (keys.length > 0) {
      text = JSON.stringify(rest, null, 2);
    } else {
      text = '(No content returned)';
    }
  }

  return (
    <div className={`response-text ${isError ? 'response-text--error' : ''}`}>
      {isError && (
        <span className="response-text__error-label label-section text-red">
          Pipeline Error
        </span>
      )}
      <div className="response-text__body">
        {text.split('\n').map((line, i) => (
          <p key={i} className={!line.trim() ? 'response-text__blank' : undefined}>
            {line || '\u00A0'}
          </p>
        ))}
      </div>
    </div>
  );
}
