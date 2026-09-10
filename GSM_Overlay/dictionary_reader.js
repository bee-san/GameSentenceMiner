const DICTIONARY_READER_YOMITAN = 'yomitan';
const DICTIONARY_READER_HACHIDORI = 'hachidori';

function normalizeDictionaryReader(value) {
  return value === DICTIONARY_READER_HACHIDORI
    ? DICTIONARY_READER_HACHIDORI
    : DICTIONARY_READER_YOMITAN;
}

module.exports = {
  DICTIONARY_READER_HACHIDORI,
  DICTIONARY_READER_YOMITAN,
  normalizeDictionaryReader,
};
