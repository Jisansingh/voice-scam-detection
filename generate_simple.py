import csv
import random

categories = ['family', 'friend_chat', 'student', 'office', 'delivery', 'shopping', 'travel', 'food', 'banking', 'customer_support', 'cab_service', 'courier', 'college', 'gaming', 'personal']

templates = {
    'family': ["arey yaar tu kaahan hai abhi kaisa hai sab", "bhaiyo aur bahno ko hello bolo wo bohot miss kar rahe hain", "mummy ne poocha tu kab ghar aayega khaana banaya hai", "papa bol rahe hain office se jaldi aana kuch kaam hai", "dadaji phone pe bohot khush hue teri awaaz sunke", "arey behen tu exam ki preparation kaisi chal rahi hai", "chacha ji ne poocha tumhara number kahaan se mila", "mausi ne naya ghar shuru kiya hai party de rahi hai", "papa ne kaha bus ticket book kar lo weekend ke liye", "arey didi tu office se late aati hai kya khana banaogi", "bhai tu market se sabzi leke aana mummy ne kaha", "nana ji ne health ke baare mein poocha darte nahi na", "arey cousin tu last week ki shaadi mein kahan gaya", "dadi ne bohot miss kiya aur video call karna"],
    'friend_chat': ["bhai kya haal hai kahan fase hue ho", "arey yaar kal movie dekhne chalte hain kaisa rahega", "tu canteen mein aaja coffee peete hain", "bhai tune naya phone liya kitna price aaya", "arey yaar placement ka result aaya pakka milgaya", "kal raat ko group mein baat karte hain bhookhe mat raho", "tu sports ground aaja cricket khelenge", "arey last semester ka result dekh liya tu topper ban gaya", "bhai library mein seat mili main bhi aana chahta hoon", "yaar cafe ki driving mil jaye toh best hai"],
    'student': ["professor ne assignment last date badha diya hai", "arey exam timetable aaya hai preparation shuru karo", "library mein seats milna mushkil ho gaya yaar", "tu chemistry ki notes share kar sakta hai", "bhai marks aaye hain portal pe check kar le", "arey sem fees online submit karni hai last date kal hai", "tu placement cell mein gaye interview dates aaye hain", "bhai project report deadline miss ho gaya kya karein", "arey mess ka food bohot kharab ho gaya hai", "tu hostel room change ke liye apply kiya"],
    'office': ["good morning sir meeting 3 baje hai", "arey report submit kar diya email bhej diya hai", "bhai client se call aaya presentation ready karo", "tu leaves ke liye application bhejna hr ne kaha", "arey project deadline this week hai machao", "sir ne naya task assign kiya hai assign kar diya", "bhai work from home ki permission mil gayi hai", "arey team meeting mein sabko invite kar diya", "tu performance review ke liye prepare karo date fix hai", "sir ne appreciation kiya project ke liye bohot khush hai"],
    'delivery': ["arey delivery boy bahar khada hai door open karo", "bhai order cancel karna hai koi issue hai", "tu order ki track kar sakta hai kahan phas gaya", "arey delivery time 10 minutes mein aayega wait karo", "package thoda damage ho gaya hai return policy check karo", "bhai cod hai ya online payment karni hai", "arey wrong item deliver ho gaya hai exchange karana hai", "order delivered successfully photo leke rakha hai", "bhai delivery partner ne call kiya location confirm karo", "arey grocery order ka bill sahi nahi aaya verify karo"],
    'shopping': ["arey sale mein bohot sasta mil raha hai shopping karo", "bhai online store pe discount code chal raha hai", "tu clothes ka size check kar exchange possible hai", "arey shoe ka colour nahi pasand return karna hai", "bhai cashback offer mil raha hai payment karo", "arey wallet ki payment fail ho gayi retry karo", "tu gift wrapping karwa sakte ho birthday gift hai", "bhai order placed ho gaya confirmation email aaya", "arey product out of stock hai notify kar denge", "shopping app ka new version download kiya fast hai"],
    'travel': ["arey flight booking confirm ho gayi pnr bhej diya", "bhai train ki waiting list confirm ho gayi", "tu hotel reservation kar liya checkin time dekho", "arey cab booked hai driver 10 minute mein aayega", "bhai travel insurance ka option hai lena chahiye", "arey boarding pass print karna hai kiosk available hai", "tu baggage allowance check kiya extra ka charge lagega", "bhai visa application status online check kar sakte hain", "arey refund mil gaya flight cancellation ke baad", "tour package ki booking kar raha hai itinerary dekho"],
    'food': ["arey zomato se order kiya 30 minute mein aayega", "bhai swiggy par discounts chal rahe hain try karo", "tu restaurant mein table book kiya confirm aaya", "arey biryani ka order place kiya jaldi aayega", "bhai buffet mein sabziyo ki variety bohot achhi hai", "arey tiffin service ki trial le raha hai first day hai", "tu home delivery ka time prefer karta hai", "bhai chinese restaurant ka recommendation chahiye", "arey cake order kiya birthday ke liye timing correct hai", "diet plan ke liye low oil ka khana milta hai kya"],
    'banking': ["arey bank ne new policy introduce kiya hai", "bhai atm ka pin change karna hai kaise karte hain", "tu online banking activate kiya secure hai", "arey account statement download kar liya verify karo", "bhai credit card ka bill due hai payment karo", "arey loan application ke liye documents submit kiye", "tu fd ka interest rate check kiya better option hai", "bhai net banking password reset kar raha hai", "arey debit card blocked ho gaya new card manga", "bank branch mein jana padega online issue resolve nahi hua"],
    'customer_support': ["arey customer care se baat karni hai representative chahiye", "bhai service request register kiya ticket number mil gaya", "tu refund status check kar sakta hai", "arey warranty claim karni hai process batayo", "bhai subscription renew karni hai payment options batado", "arey product defect ki complaint kar raha hoon", "tu chat support use kar sakte ho quick response milta hai", "bhai service charge ki details chahiye breakdown do", "arey installation appointment book karni hai", "tu return policy ke baare mein batao kitne days mein refund"],
    'cab_service': ["arey cab booked hai driver 5 minute mein aayega", "bhai ride cancel karni hai reason select karo", "tu driver ko call kar sakta hai pickup point confirm karo", "arey ride fare estimate dekho meter se kam aayega", "bhai ride completed rating dena mat bhoolna", "arey extra stops add karni hai driver se baat karo", "tu outstation ride ke liye package check karo", "bhai cab type select karo sedan ya suv", "arey driver ne route change kiya reason pocho", "ride mein item forgot kar diya lost and found contact karo"],
    'courier': ["arey courier booked hai pickup tomorrow aayega", "bhai tracking number check karo live location dekho", "tu package deliver kar diya receiver ne sign kiya", "arey delivery delayed hai weather ke karan hai", "bhai international shipping ka charges calculate karo", "arey fragile item hai proper packing karo", "courier boy ne call kiya address confirm karo", "bhai oders ki delivery 2 days mein hogi", "arey wrong address diya hai correction karo", "package lost ho gaya hai complaint file karo"],
    'college': ["arey college fest mein participation karni hai", "bhai attendance percentage maintain karna hai", "tu club meetings mein attend karta hai", "arey college bus route check kiya timing dekho", "bhai semester registration last week hai form fill karo", "arey library card renew karni hai last date kal hai", "tu college canteen ka food card recharge kiya", "bhai department mein seminar hai attendance mandatory hai", "arey alumni meet ke liye registration open hai", "tu sports trials mein part lena hai"],
    'gaming': ["arey bgmi mein squad match khelenge", "bhai free fire ka new event shuru ho gaya hai", "tu cs go mein rank improve kiya", "arey valorant ka new agent aaya hai try kiya", "bhai pubg mobile mein season reset ho gaya", "arey gaming phone lena chahiye performance better hai", "tu steam sale mein game khareeda discount mila", "bhai online tournament mein register kiya", "arey gaming headphones ki recommendation chahiye", "tu stream kar raha hai viewer count kaisa hai"],
    'personal': ["arey kaisa hai tu koi update hai", "bhai kaal se call nahi hui busy tha kya", "tu apna time manage kar raha hai schedule banao", "arey future ki planning kar raha hoon suggestions chahiye", "bhai health checkup karaya report aayi hai", "arey new hobby shuru karni hai kya suggest karoge", "tu self improvement ke liye kya kar raha hai", "bhai meditation shuru kiya mental health important hai", "arey daily routine maintain kar raha hoon disciplined hoon", "tu relationships ke baare mein kaisa feel kar raha hai"]
}

def get_lang(text):
    hi = sum(1 for c in text if ord(c) >= 2304 and ord(c) <= 2416)
    if hi > len(text) * 0.3:
        return 'hi'
    elif hi > 0:
        return 'hinglish'
    return 'en'

rows = []
for cat in categories:
    base_texts = templates[cat]
    for base in base_texts:
        rows.append({'text': base.lower(), 'label': '0', 'category': cat, 'language': get_lang(base), 'tactics': 'none'})
    needed = 50 - len(base_texts)
    for _ in range(needed):
        base = random.choice(base_texts)
        parts = base.split()
        random.shuffle(parts)
        new_text = ' '.join(parts)
        rows.append({'text': new_text.lower(), 'label': '0', 'category': cat, 'language': get_lang(new_text), 'tactics': 'none'})

seen = set()
unique = []
for r in rows:
    if r['text'] not in seen:
        seen.add(r['text'])
        unique.append(r)

with open('./dataset/conversations.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['text', 'label', 'category', 'language', 'tactics'])
    w.writeheader()
    w.writerows(unique)

print(f"Saved {len(unique)} rows")