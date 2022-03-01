import re


import requests
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize, stanford, regexp_span_tokenize
try:
    from nltk.tokenize import sent_tokenize, wordpunct_tokenize
except LookupError:
    pass

class PubmedMention:
    def __init__(self, **kwargs):
        self._raw = kwargs
        self._mention = kwargs['mention']
        self._mesh_id = "MESH:" + kwargs['mesh_id']
        self._umls_ids = [f"UMLS:{i}" for i in kwargs['link_id'].split('|')]
        self._start_offset = kwargs['start_offset']
        self._end_offset = kwargs['end_offset']
        # set default to named thing and mesh id
        self._biolink_type = "biolink:NamedThing"
        self._biolink_id = self._mesh_id
        self.is_normalized = False


    def set_normalized(self, nn_output):
        # Uses https://nodenormalization-sri.renci.org/1.2/get_normalized_nodes
        # to get biolinkified type
        normalized = nn_output.get(self._mesh_id, None)
        if normalized:
            self.is_normalized = True
            self._biolink_id = normalized['id']['identifier']
            self._biolink_type = normalized['type'][0]

    def __str__(self):
        return f"{self._mention} , {self._biolink_type} , {self._biolink_id}"



class PubMedJson:
    def __init__(self, **kwargs):
        self._raw = kwargs
        self._text = self._raw['text']
        self._mentions = [PubmedMention(**x) for x in self._raw['mentions']]
        self.normalize_mentions()

    def __str__(self):
        mention_strs = '\n'.join([x.__str__() for x in self._mentions])
        return f'Article Title: {self._raw["title"]}\n' \
               f'mentions : {mention_strs}'

    def get_mesh_ids(self):
        return [ mention._mesh_id for mention in self._mentions]

    def to_IOB_format(self):
        # this loooks bad , maybe there a better way of tokenizing sentences
        # abbrevations or other usage of `.` might result skewed sentences.
        print(len(self._text))
        print(self._text)
        sentences = sent_tokenize(self._text)
        sum = 0
        for s in sentences:
            for words in wordpunct_tokenize(s):
                sum += len(words)

        print(sum)
        iob_tagged = []
        for sentence in sentences:
            iob_tagged.append(self.tag_labels(sentence))
        return [" ".join(wordpunct_tokenize(x)) + '\n' for x in sentences], [x + '\n' for x in iob_tagged]

    def normalize_mentions(self):
        mesh_ids = [mention._mesh_id for mention in self._mentions]
        nn_url = "https://nodenormalization-sri.renci.org/get_normalized_nodes"
        response = {}
        for i in range(0, len(mesh_ids), 10):
            http_response = requests.post(nn_url, json= {"curies": mesh_ids[i:i+10]})

            if http_response.status_code != 200:
                retry_end = False
                count = 0
                # retry
                while http_response.status_code == 500 or not retry_end:
                    print("failed retrying")
                    http_response = requests.post(nn_url, json={"curies": mesh_ids[i:i+10]})
                    count += 1
                    retry_end = count == 2
            response.update(http_response.json())


        for mention in self._mentions:
            mention.set_normalized(response)

    def tag_labels(self, sentence):
        words = list(wordpunct_tokenize(sentence))
        labels = {}
        for word_pos, word in enumerate(words):
            for mention in self._mentions:
                words_in_mention = wordpunct_tokenize(self._text[mention._start_offset:mention._end_offset])
                if len(words_in_mention) == 1:
                    if word.lower() == words_in_mention[0].lower():
                        labels[word_pos] = "B-" + mention._biolink_type
                else:
                    matches_found = 0
                    temp_labels = {}
                    for index, word_in_mention in enumerate(words_in_mention):
                        if len(words) > word_pos + index:
                            if word_in_mention.lower() == words[word_pos + index]:
                                matches_found += 1
                                if index == 0:
                                    temp_labels[word_pos + index] = f"B-{mention._biolink_type}"
                                else:
                                    temp_labels[word_pos + index] = f"I-{mention._biolink_type}"
                    if matches_found == len(words_in_mention):
                        labels.update(temp_labels)
        iob_labels = ["0" for x in words]

        for index in labels:
            iob_labels[index] = labels[index]
        return " ".join(iob_labels)





if __name__ == '__main__':
    x =  {"_id": "7830505", "text": "Purinergic and cholinergic components of bladder contractility and flow. The role of ATP as a neurotransmitter/neuromodulator in the urinary tract has been the subject of much study, particularly whether ATP has a functional role in producing urine flow. Recent studies suggested significant species variation, specifically a variation between cat and other species. This study was performed to determine the in vivo response of cat urinary bladder to pelvic nerve stimulation (PNS) and to the exogenous administration of cholinergic and purinergic agents. In anesthetized cats, bladder contractions and fluid expulsion was measured in response to PNS and to the exogenous administration of cholinergic and purinergic agents. Fluid was instilled into the bladder and any fluid expelled by bladder contractions induced by PNS or exogenous agents was collected in a beaker. The volume was measured in a graduated cylinder and recorded. PNS, carbachol and APPCP produced sustained contractions with significant expulsion of fluid. ATP, ACh and hypogastric nerve stimulation did not produce any significant expulsion of fluid. Atropine, a cholinergic antagonist, inhibited PNS contractions and fluid expulsion with no effect on purinergic actions. There was a significant relationship between the magnitude of the contraction, duration of the contractions and volume of fluid expelled. The data and information from other studies, strongly suggests a functional role for ATP as a cotransmitter in the lower urinary tract different from ACh's role. ATP stimulation of a specific purinergic receptor plays a role in initiation of bladder contractions and perhaps in the initiation of urine flow from the bladder. ACh's role is functionally different and appears to be more involved in maintenance of contractile activity and flow.", "title": "Purinergic and cholinergic components of bladder contractility and flow.",
          "mentions": [{"mention": "urinary bladder", "start_offset": 433, "end_offset": 448, "link_id": "C0225358|C0005682", "mesh_id": "D001743"},
                       {"mention": "cats", "start_offset": 573, "end_offset": 577, "link_id": "C0007450", "mesh_id": "D002415"}]}

    pubmed_model = PubMedJson(**x)
    text, labels  = pubmed_model.to_IOB_format()
    for sentence, labeled in zip(text, labels):
        print('_--------------------------')
        print(sentence)
        print(labeled)
        assert(len(sentence.split(' '))) == len(labeled.split(" "))