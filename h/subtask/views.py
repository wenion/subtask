from pyramid.view import view_config

@view_config(route_name='hello', request_method='GET', renderer='json')
def hello_world(request):
    return {'hello': 'world!'}


data = [
    {
        'content': 'Description Towers of Hanoi (Part 2) Puzzle components include: disk will be represented by a positive int corresponding to the size of the disk. For example, if there are 4 disks, the disks (from smallest to the largest) will be represented by the integers 1, 2, 3 and 4, respectively. needle will be represented by a list of int corresponding to disks from bottom to top. For example, lists [4,3], [2,1] and [] represent the needles 0, 1 and 2 visualised below. state will be represented by a list of 3 lists corresponding to needles from left to right. For example, the list of 3 lists [[4,3],[2,1],[]] represents the state visualised above. Question 1 Write a function named start_state that inputs the number of disks n, and outputs the start state of the puzzle (i.e., all disks are on needle 0 where the disks are ordered from smallest to the largest from top to bottom). Expand Question 2 Write a function named aux that inputs two integers representing the needles, and outputs the other needle. Expand Question 3 Write a function named next_state that inputs i) the needle the disk moves from, ii) the needle the disk moves to and iii) the current state of the puzzle, and outputs the next state of the puzzle (i.e., as a result of moving the disk). Only the top disk is moved if there are multiple disks on a given needle. Expand Do NOT mutate the input list state. You do NOT need to use recursion to solve Questions 1-3. Description Use left and right arrow keys to adjust the split region size hanoi.py 1 /home/hanoi.py Spaces: 4 (Auto) Changes will not be saved. Reload Use up and down arrow keys to adjust the split region size Console Terminal Run',
        'title': 'FIT1045_FIT1053 S1 2023_Week 11 - Advanced Python_W11 Applied_Towers of Hanoi (Part 2).json',
        'summary': 'The summary is about a puzzle called Towers of Hanoi, which involves moving disks between needles. The puzzle components are represented by positive integers and lists. The questions involve creating functions to determine the start state of the puzzle, find the other needle given two needles, and determine the next state of the puzzle when a disk is moved. The input list should not be mutated and recursion is not required for solving the questions.',
        'url': 'https://edstem.org/au/courses/10682/lessons/31246/slides/248634',
        'repository': 'Ed'
    },
    {
        'content': 'Description Guess the secret number (iterative) In this activity we will combine a while loop and an if-elif-else, both seen in the pre-class activities. Question 1 (✓) Using a while loop, write a program that: Prompts "Enter guess: " and reads an integer input, Prints "Good guess!" if the number is 42, and terminates the program, Prints "Too high" if the number is greater than 42, and go back to step 1, Prints "Too low" if the number is smaller than 42, and go back to step 1. Hint Expand Question 2 (requires no further knowledge) Expand Sample input and output Description Use left and right arrow keys to adjust the split region size guess.py 1 2 3 4 5 #guess = int(input("Enter guess: ")) #print("Good guess!") #print("Too high") #print("Too low") /home/guess.py Spaces: 4 (Auto) All changes saved Use up and down arrow keys to adjust the split region size Console Terminal Run Mark',
        'title': 'FIT1045 OCT 2023 MUM_Week 02 - Conditionals and Iteration (while loops)_W2 Workshop_Guess the secret number (iterative).json',
        'summary': 'This activity involves writing a program that prompts the user to guess a secret number. If the guess is correct, the program terminates. If the guess is too high or too low, the program prompts the user to guess again. The program uses a while loop and an if-elif-else statement.',
        'url': 'https://edstem.org/au/courses/14043/lessons/44038/slides/300725',
        'repository': 'Ed'
    },
    {
        'content': '16 May - 22 May Week 11 - Cases of MML Week 11 text.L1 File Hidden from students text.L2 File Hidden from students Assignment 4 (due date Oct 21st) - Machine Translation File Hidden from students Clustering notes File 518.4KB PDF document Hidden from students Assignment 4 -- feature selection / clustering File 118.2KB PDF document Hidden from students Data for Assignment 4 Folder Hidden from students Simply MML Cases File 2.1MB PDF document Multivariable MML Cases File 1.5MB PDF document',
        'title': 'FIT4009 Advanced topics in intelligent systems S1 2016_section-12.json',
        'summary': 'In the given week, there were cases related to MML, assignment 4 on machine translation and feature selection/clustering, as well as notes and data for assignment 4. There were also documents on Simply MML and Multivariable MML cases.',
        'url': 'https://lms.monash.edu/course/view.php?id=28319#section-12',
        'repository': 'Moodle'
    },
    {
        'content': '3.1 Working with DATE functions Date functions insert or calculate dates and times For scheduling or determining on what days of the week certain dates occur',
        'title': 'FIT1013 S2 2023_Week 1_Week 1 Pre-class Activity_3.1 Working with DATE functions.json',
        'summary': 'Date functions are used to insert or calculate dates and times, which can be helpful for scheduling or determining the days of the week certain dates occur.',
        'url': 'https://edstem.org/au/courses/12884/lessons/39117/slides/271188',
        'repository': 'Ed'
    },
    {
        'content': 'Huffman code Huffman invented a greedy algorithm that constructs an optimal prefix-free code, called a Huffman code in his honor. Its proof of correctness relies on the greedy-choice property and optimal substructure, which is beyond the scope of our unit (you will see this in FIT2004). Because of this, we will not discuss the correctness of this algorithm but we will rather demonstrate how it works. The procedure huffman() assumes that  C is a set of  n characters and that each character  c∈C is an object with an attribute  c.freq giving its frequency. The algorithm builds the tree corresponding to an optimal code in a bottom-up manner. It begins with a set of  ∣C∣ leaves and performs a sequence of  ∣C∣−1 "merging" operations to create the final tree. The algorithm uses a min-priority queue  Q, keyed on the  freq attribute, to identify the two least-frequent objects to merge together. The result of merging two objects is a new object whose frequency is the sum of frequencies of the two objects that were merged. The idea of Huffman\'s algorithm is as simple as that! It creates a coding binary tree in bottom-up manner by utilising a priority queue. You are already familiar with both of these concepts. In the following, we provide an implementation of the algorithm. The following implementation may look complicated because we rely on heavy use of Python\'s internal functionality. This is done for the sake of succinctness. Note that a similar implementation could be made using binary tree and heap-based min-priority queue implementations from the previous weeks! Example: For our above example the Huffman\'s algorithm proceeds as shown in the following figure. Since the alphabet contains  6 letters, the initial queue size is  n=6, and 5 merge steps build the result Huffman tree. The final tree represents the optimal prefix-free code. Each part of the figure shows the contents of the queue sorted into increasing order by frequency. Each step merges the two trees with the lowest frequencies. Leaves are shown as rectangles containing a character and its frequency. Internal nodes are shown as circles containing the sum of the frequencies of their children. An edge connecting an internal node with its children is labeled  0 if it is an edge to a left child and  1 if it is an edge to a right child. The codeword for a letter is the sequence of labels on the edges connecting the root to the leaf for that letter. (a) The initial set of nodes, one for each letter. (b)–(e) Intermediate stages. (f) The final Huffman tree. Run PYTHON 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 def huffman(text):     # get all character frequencies in the text     freqs = [Node(char=c, freq=f) for c, f in Counter(text).items()]     # create a binary min-heap of all frequencies     heapify(freqs)     # main loop: bottom-up Huffman tree construction     for i in range(len(freqs) - 1):         x = getmin(freqs) # get 1\'st smallest         y = getmin(freqs) # get 2\'nd smallest         # create a new node; its frequency is the sum         z = Node(char=(x, y), freq=x.freq + y.freq) The huffman() procedure works as follows. It receives a sequence of characters, i.e. text, and returns the root node of the result Huffman tree. Line 3 initialises the list freqs of leaf nodes of the future tree containing the characters to be encoded with their frequencies in the given text. Note that the number of elements of the list equals  n=∣C∣. Then line 6 heapifies the list freqs, i.e. it becomes a min-heap-sorted queue (the node with lowest frequency goes first). The for loop in lines 9-16 repeatedly extracts the two nodes  x and  y of lowest frequency from the queue and replaces them in the queue with a new node  z representing their merger, see line 16. The frequency of  z is computed as the sum of the frequencies of  x and  y in line 14. The new node  z has as its left child  x and as its right child  y, represented as a Python tuple (x, y). (We should say that this order is arbitrary. Switching the left and right child of any node yields a different code of the same cost.) After  n−1 mergers, the loop stops and line 19 returns the one node left in the queue, which is the root of the Huffman code tree. We recommend you to play with this implementation and see how its particular parts are done. Also, make sure you run it, enter some text to encode, and check the output! Complexity The running time of Huffman’s algorithm depends on how the min-priority queue freqs is implemented. Let’s assume that it is implemented as a binary min-heap (this is how it is done in our implementation). For a set  C of  n characters, the heapify() procedure runs in  O(n) time as was discussed in the lesson of the previous week (recall bottom-up heap construction). The for loop in lines 9-16 executes exactly  n−1 times, and since each heap operation runs in  O(logn) time, the loop contributes  O(n⋅logn) to the overall running time. Thus, the total running time of huffman() on a set of  n characters is  O(n⋅logn). This complexity applies both in the best- and worst-case scenarios. Also, note that if we start from a piece of text  T of length  m such that there are  n≤m distinct characters, then we should not forget that computing the frequencies for all the  n characters can be done in  O(m) time as we need to traverse the entire text  T of size  m and update  n counters (a counter per distinct character) accordingly.',
        'title': 'FIT1008_FIT1054_FIT2085 S2 2023_Week 12 [NOT ASSESSABLE] - Beyond FIT1008: Fundamental Algorithms and Applications (string matching, data compression, and Bloom filters)_12.0 - Week 12 - Pre-Reading_Huffman code.json',
        'summary': "The summary explains that Huffman invented a greedy algorithm called Huffman code, which constructs an optimal prefix-free code. The algorithm builds a tree in a bottom-up manner by merging the two least-frequent objects using a min-priority queue. The implementation provided uses Python's internal functionality. The complexity of the algorithm is O(n*logn), where n is the number of characters. Computing the frequencies of the characters can be done in O(m) time, where m is the length of the text.",
        'url': 'https://edstem.org/au/courses/12108/lessons/36829/slides/257096',
        'repository': 'Ed'
    },
    {
        'content': "Section 10 Hidden from students Week 10 Sony fined $1.5M over fake film reviews URL Sony (again) in trouble for fake viral videos URL Tsumea list of Australian game developers URL ______________________ Physics as gameplay URL What's wrong with the game industry URL Advice on setting up your own game company URL",
        'title': 'FIT2073 Game design and narrative S1 2014_section-10.json',
        'summary': 'In section 10, Sony is fined $1.5M for fake film reviews and is also in trouble for fake viral videos. A list of Australian game developers is provided, along with information on incorporating physics in gameplay. The article discusses issues in the game industry and offers advice on setting up a game company.',
        'url': 'https://lms.monash.edu/course/view.php?id=15367#section-10',
        'repository': 'Moodle'
    },
    {
        'content': '◀︎Exam (28 Oct - 24 Nov) Resources (Staff Only) Hidden from students Staff resources Learning systems staff resources URL Moodle support URL Copyright and teaching Page Engagement Analytics URL ◀︎Exam (28 Oct - 24 Nov)',
        'title': 'FIT3138 Real time enterprise systems S2 2019_section=21.json',
        'summary': 'This message provides a list of exam resources that are only accessible to staff members. It includes a link for Moodle support, information on copyright and teaching, and a URL for engagement analytics. The resources are available for a specific period of time from October 28th to November 24th.',
        'url': 'https://lms.monash.edu/course/view.php?id=56269&section=21',
        'repository': 'Moodle'
    },
    {
        'content': 'Untitled',
        'title': 'FIT9136 S1 2023 - Workshop Activities - Untitled',
        'summary': 'The summary is not provided as the content of the text is missing.',
        'url': 'https://edstem.org/au/courses/10696/lessons/31360/slides/235327',
        'repository': 'Ed-json'
    },
    {
        'content': "◀︎Workshop 3\nStudent Resources▶︎\nForums\nThis section contains:\nAnnouncement\nDiscussion Forums\nAnnouncements\nUnit Announcements\nForum\nDiscussions\nGeneral Discussion MDP E-1\nForum\nGeneral Discussion MDP E-2\nForum\nPre-Workshop 1 Activities\nForum\n◀︎Workshop 3\nStudent Resources▶︎",
        'title': 'MDP Ethical Research in IT - Forums',
        'summary': 'This section contains various forums for announcements and discussions related to Workshop 3 and student resources.',
        'url': 'https://lms.monash.edu/course/view.php?id=159450&section=4',
        'repository': 'Moodle-json'
    }
]

# @view_config(route_name='query', request_method='GET', renderer='json')
# def query(request):
#     querying = request.params.get("q")
#     return data


@view_config(route_name='query', request_method='GET', renderer='json')
def query(request):
    kn = request.registry['kn']
    topics, status = [], '200'
    querying = request.params.get("q")
    if not querying:
        return {'status': status, 'query': querying, 'context': topics}
    try:
        response_list = kn.query_retrieval_optimised([querying])

        for topic in response_list:
            results = []
            for i, (doc, score) in enumerate(topic):
                m = doc.metadata
                summary = m.get("summary", "")
                if isinstance(summary, dict) and 'input_documents' in summary:
                    m["summary"] = summary.get("output_text", m.get("url", ""))
                results.append({'id': i, 'page_content': doc.page_content, 'metadata': m, 'score': score})
            topics.append(results)
    except Exception as e:
        status = str(e)
    top20 = topics[0][:20] if topics else []
    return {'status': status, 'query': querying, 'context': top20}

@view_config(route_name='knowledge', request_method='POST', renderer='json')
def knowledge_pushing(request):
    try:
        kn = request.registry['kn']
        content = request.POST.get('content')

        if not content:
            return {'error': 'Missing content'}

        summary, response_list = kn.knowledge_pushing(content)
        topics = []
        for topic in response_list:
            results = []
            for i, (doc, score) in enumerate(topic):
                m = doc.metadata
                if isinstance(m.get("summary", {}), dict):
                    m["summary"] = m["summary"].get("output_text", m.get("title", ""))
                results.append({'id': i, 'page_content': doc.page_content, 'metadata': m, 'score': score})
            topics.append(results)
            top5 = topics[0][:5] if topics else []
        return {'summary': summary, 'context': top5}

    except Exception as e:
        import traceback
        traceback.print_exc()  # ✅ logs error to terminal
        return {'error': str(e)}

@view_config(route_name='upload', request_method='POST', renderer='json')
def knowledge_upload(request):
    kn = request.registry['kn']
    doc_dict = {
        "Title": request.POST.get('title'),
        "Content": request.POST.get('content'),
        "URL": request.POST.get('url'),
        "Repository": request.POST.get('repository')
    }
    if not doc_dict["Content"]:
        return {"fail": "Content is empty"}

    try:
        count =  kn.nuggets_update([doc_dict])
        if count > 0:
            return {"success": True, "message": f"{count} document(s) added"}
        else:
            return {"success": False, "message": "No document added (possibly empty or invalid)"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
