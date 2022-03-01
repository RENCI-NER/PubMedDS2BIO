from src.Models import PubMedJson
import json
from functools import reduce

def stream(input_file, output_file, format):
    if format == 'IOB':
        output_txt = output_file + '.txt'
        output_labels = output_file + '.labels.txt'
        all_labels = set()
        with open(input_file, 'r') as stream:
            with open(output_txt, 'w') as out_txt_stream:
                with open(output_labels,'w') as out_labels_stream:
                    for line in stream:
                        pubmed_json_object = PubMedJson(**json.loads(line))
                        sentences, labels = pubmed_json_object.to_IOB_format()
                        for m in reduce(lambda m, y: m + y , [[x for x in i.strip('\n').split(' ') if x != '0'] for i in labels], []):
                            all_labels.add(m)
                        out_txt_stream.writelines(sentences)
                        out_labels_stream.writelines(labels)
        with open('categories.txt', 'w') as stream:
            stream.writelines(all_labels)









