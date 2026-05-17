import csv
import random
import re

categories = [
    'family', 'friend_chat', 'student', 'office', 'delivery', 'shopping',
    'travel', 'food', 'banking', 'customer_support', 'cab_service',
    'courier', 'college', 'gaming', 'personal'
]

family_templates = [
    "arey yaar tu kaahan hai abhi, kaisa hai sab?",
    "bhaiyo aur bahno ko hello bolo, wo bohot miss kar rahe hain",
    "mummy ne poocha tu kab ghar aayega, khaana banaya hai",
    "papa bol rahe hain office se jaldi aana, kuch kaam hai",
    "dadaji phone pe bohot khush hue teri awaaz sunke",
    "arey behen tu exam ki preparation kaisi chal rahi hai?",
    "chacha ji ne poocha tumhara number kahaan se mila",
    "mausi ne naya ghar shuru kiya hai, party de rahi hai",
    "papa ne kaha bus ticket book kar lo weekend ke liye",
    "arey didi tu office se late aati hai, kya khana banaogi?",
    "bhai tu market se sabzi leke aana, mummy ne kaha",
    "nana ji ne health ke baare mein poocha, darte nahi na?",
    "arey cousin tu last week ki shaadi mein kahan gaya?",
    "dadi ne bohot miss kiya, aur video call karna",
    "arey mummy ne permission diya hai, tu ja sakta hai"
]

friend_chat_templates = [
    "bhai kya haal hai, kahan fase hue ho?",
    "arey yaar kal movie dekhne chalte hain, kaisa rahega?",
    "tu canteen mein aaja, coffee peete hain",
    "bhai tune naya phone liya? Kitna price aaya?",
    "arey yaar placement ka result aaya, pakka milgaya",
    "kal raat ko group mein baat karte hain, bhookhe mat raho",
    "tu sports ground aaja, cricket khelenge",
    "arey last semester ka result dekh liya tu topper ban gaya",
    "bhai library mein seat mili? Main bhi aana chahta hoon",
    "yaar cafe ki driving mil jaye toh best hai",
    "arey tu assignment bana raha hai? Share kar de",
    "bhai festival mein ghar ja raha hai? Train milta hai?",
    "tu canteen se samosa leke aaja, bohot bhookh lagi hai",
    "arey yaar tu kaisi ho, kaal se call nahi kiya",
    "bhai hostel mein wifi kaafi slow hai, kya kar rahe ho?"
]

student_templates = [
    "professor ne assignment last date badha diya hai",
    "arey exam timetable aaya hai, preparation shuru karo",
    "library mein seats milna mushkil ho gaya hai yaar",
    "tu chemistry ki notes share kar sakta hai?",
    "bhai marks aaye hain portal pe, check kar le",
    "arey sem fees online submit karni hai, last date kal hai",
    "tu placement cell mein gaye? Interview dates aaye hain",
    "bhai project report deadline miss ho gaya, kya karein?",
    "arey mess ka food bohot kharab ho gaya hai",
    "tu hostel room change ke liye apply kiya?",
    "bhai scholarship form last week tak last date hai",
    "arey tuition fees installment ki facility milti hai kya?",
    "tu fests mein volunteer karna hai? Registration open hai",
    "bhai practical exam ki date change ho gayi hai",
    "arey attendance ki problem hai, professor ne bataya"
]

office_templates = [
    "good morning sir, meeting 3 baje hai",
    "arey report submit kar diya, email bhej diya hai",
    "bhai client se call aaya, presentation ready karo",
    "tu leaves ke liye application bhejna, hr ne kaha",
    "arey project deadline this week hai, machao",
    "sir ne naya task assign kiya hai, assign kar diya",
    "bhai work from home ki permission mil gayi hai",
    "arey team meeting mein sabko invite kar diya",
    "tu performance review ke liye prepare karo, date fix hai",
    "sir ne appreciation kiya project ke liye, bohot khush hai",
    "bhai office ke naye rules ke baare mein pocho hr se",
    "arey salary slip download kar liya? Issues aa rahi hai",
    "tu new joinee ka training karayega, schedule banao",
    "bhai client feedback aaya hai, improve karna padega",
    "arey office supplies ka order karna hai, list bhejo"
]

delivery_templates = [
    "arey delivery boy bahar khada hai, door open karo",
    "bhai order cancel karna hai, koi issue hai",
    "tu order ki track kar sakta hai? Kahan phas gaya?",
    "arey delivery time 10 minutes mein aayega, wait karo",
    "package thoda damage ho gaya hai, return policy check karo",
    "bhai COD hai ya online payment karni hai?",
    "arey wrong item deliver ho gaya hai, exchange karana hai",
    "order delivered successfully, photo leke rakha hai",
    "bhai delivery partner ne call kiya, location confirm karo",
    "arey grocery order ka bill sahi nahi aaya, verify karo",
    "express delivery ka extra charge lagta hai, sure ho jao",
    "bhai delivered item ka quality bohot achhi hai",
    "arey delivery slot change karna hai, available hai kya?",
    "order return kiya hai, refund kab aayega?",
    "bhai customer care se baat karni hai, number do"
]

shopping_templates = [
    "arey sale mein bohot sasta mil raha hai, shopping karo",
    "bhai online store pe discount code chal raha hai",
    "tu clothes ka size check kar, exchange possible hai",
    "arey shoe ka colour nahi pasand, return karna hai",
    "bhai cashback offer mil raha hai, payment karo",
    "arey wallet ki payment fail ho gayi, retry karo",
    "tu gift wrapping karwa sakte ho? Birthday gift hai",
    "bhai order placed ho gaya, confirmation email aaya",
    "arey product out of stock hai, notify kar denge",
    "shopping app ka new version download kiya, fast hai",
    "bhai wishlist mein add kiya hai, price drop aayi toh batana",
    "arey festival sale mein online payment offer mil raha hai",
    "return kiya hai, store credit mil jayega",
    "bhai exchange karne aaye, new size available hai?",
    "arey loyalty points redeem kar sakte hain, check karo"
]

travel_templates = [
    "arey flight booking confirm ho gayi, pnr bhej diya",
    "bhai train ki waiting list confirm ho gayi",
    "tu hotel reservation kar liya? Check-in time dekho",
    "arey cab booked hai, driver 10 minute mein aayega",
    "bhai travel insurance ka option hai, lena chahiye",
    "arey boarding pass print karna hai, kiosk available hai",
    "tu baggage allowance check kiya? Extra ka charge lagega",
    "bhai visa application status online check kar sakte hain",
    "arey refund mil gaya flight cancellation ke baad",
    "tour package ki booking kar raha hai, itinerary dekho",
    "bhai honeymoon trip ka plan ban raha hai, destinations suggest karo",
    "arey domestic flight ka fare bohot badh gaya hai",
    "tu railway station pickup kar raha hai, time confirm karo",
    "bhai travel agent se deal karna better hai",
    "arey last minute cancellation ki policy check karo"
]

food_templates = [
    "arey zomato se order kiya, 30 minute mein aayega",
    "bhai swiggy par discounts chal rahe hain, try karo",
    "tu restaurant mein table book kiya? Confirm aaya",
    "arey biryani ka order place kiya, jaldi aayega",
    "bhai buffet mein sabziyo ki variety bohot achhi hai",
    "arey tiffin service ki trial le raha hai, first day hai",
    "tu home delivery ka time prefer karta hai?",
    "bhai chinese restaurant ka recommendation chahiye",
    "arey cake order kiya birthday ke liye, timing correct hai",
    "diet plan ke liye low oil ka khana milta hai kya?",
    "bhai pizza par extra cheese ka option hai, add karo",
    "arey food item allergic hai, ingredients check karo",
    "tu paneer ki sabji ka quantity badha sakte ho?",
    "bhai combo meal ki price affordable hai, value for money",
    "arey drinks ka menu dekhna hai, shakes available hain?"
]

banking_templates = [
    "arey bank ne new policy introduce kiya hai",
    "bhai atm ka pin change karna hai, kaise karte hain?",
    "tu online banking activate kiya? Secure hai",
    "arey account statement download kar liya, verify karo",
    "bhai credit card ka bill due hai, payment karo",
    "arey loan application ke liye documents submit kiye",
    "tu fd ka interest rate check kiya? Better option hai",
    "bhai net banking password reset kar raha hai",
    "arey debit card blocked ho gaya, new card manga",
    "bank branch mein jana padega, online issue resolve nahi hua",
    "bhai upi payment fail ho gaya, retry karo",
    "arey minimum balance maintain karni hai, charges na lage",
    "tu credit score check kiya? Improved hai",
    "bhai wallet add money kar raha hai, limit dekho",
    "arey sms alerts activate ki hain, transaction notify hoga"
]

customer_support_templates = [
    "arey customer care se baat karni hai, representative chahiye",
    "bhai service request register kiya, ticket number mil gaya",
    "tu refund status check kar sakta hai?",
    "arey warranty claim karni hai, process batayo",
    "bhai subscription renew karni hai, payment options batado",
    "arey product defect ki complaint kar raha hoon",
    "tu chat support use kar sakte ho, quick response milta hai",
    "bhai service charge ki details chahiye, breakdown do",
    "arey installation appointment book karni hai",
    "tu return policy ke baare mein batao, kitne days mein refund?",
    "bhai technical issue hai, engineer dispatch karo",
    "arey premium plan upgrade karni hai, benefits batayo",
    "tu query resolve ho gaya? Feedback dena hoga",
    "bhai escalation karni hai, manager se baat chahiye",
    "arey self service portal pe registration karo"
]

cab_service_templates = [
    "arey cab booked hai, driver 5 minute mein aayega",
    "bhai ride cancel karni hai, reason select karo",
    "tu driver ko call kar sakta hai, pickup point confirm karo",
    "arey ride fare estimate dekho, meter se kam aayega",
    "bhai ride completed, rating dena mat bhoolna",
    "arey extra stops add karni hai, driver se baat karo",
    "tu outstation ride ke liye package check karo",
    "bhai cab类型 select karo, sedan ya suv",
    "arey driver ne route change kiya, reason pocho",
    "ride mein item forgot kar diya, Lost and Found contact karo",
    "bhai trip summary dekho, fare breakdown hai",
    "arey peak time pricing lagta hai, normal se zyada",
    "tu share ride join kar sakta hai, fare split hoga",
    "bhai wheel chair accessibility option chahiye",
    "arey booking confirm ho gayi, driver details bheje gaye"
]

courier_templates = [
    "arey courier booked hai, pickup tomorrow aayega",
    "bhai tracking number check karo, live location dekho",
    "tu package deliver kar diya, receiver ne sign kiya",
    "arey delivery delayed hai, weather ke karan hai",
    "bhai international shipping ka charges calculate karo",
    "arey fragile item hai, proper packing karo",
    "courier boy ne call kiya, address confirm karo",
    "bhai oders ki delivery 2 days mein hogi",
    "arey wrong address diya hai, correction karo",
    "package lost ho gaya hai, complaint file karo",
    "bhai insurance add karna hai, extra safety ke liye",
    "arey bulk shipment ki discount milti hai kya?",
    "courier partner ne damage report kiya, claim process batayo",
    "bhai delivery time slot book kar sakte hain",
    "arey pod copy required hai, download karo"
]

college_templates = [
    "arey college fest mein participation karni hai?",
    "bhai attendance percentage maintain karna hai",
    "tu club meetings mein attend karta hai?",
    "arey college bus route check kiya? Timing dekho",
    "bhai semester registration last week hai, form fill karo",
    "arey library card renew karni hai, last date kal hai",
    "tu college canteen ka food card recharge kiya?",
    "bhai department mein seminar hai, attendance mandatory hai",
    "arey alumni meet ke liye registration open hai",
    "tu sports trials mein part lena hai?",
    "bhai cultural events mein entry fee hai, submit karo",
    "arey hostel mess menu change kiya, feedback do",
    "tu college wifi password liya? Username register karo",
    "bhai exam form last date miss ho gaya, late fee lag sakta hai",
    "arey placement drive ka pre registration karna hai"
]

gaming_templates = [
    "arey bgmi mein squad match khelenge?",
    "bhai free fire ka new event shuru ho gaya hai",
    "tu cs go mein rank improve kiya?",
    "arey valorant ka new agent aaya hai, try kiya?",
    "bhai pubg mobile mein season reset ho gaya",
    "arey gaming phone lena chahiye, performance better hai",
    "tu steam sale mein game khareeda? Discount mila?",
    "bhai online tournament mein register kiya?",
    "arey gaming headphones ki recommendation chahiye",
    "tu stream kar raha hai? Viewer count kaisa hai?",
    "bhai in-game purchases ka offer chal raha hai",
    "arey esports team join karni hai, trials hain",
    "tu gaming setup upgrade kar raha hai?",
    "bhai controller ka issue hai, replacement chahiye",
    "arey mobile mein lag ho raha hai, settings change karo"
]

personal_templates = [
    "arey kaisa hai tu, koi update hai?",
    "bhai kaal se call nahi hui, busy tha kya?",
    "tu apna time manage kar raha hai? Schedule banao",
    "arey future ki planning kar raha hoon, suggestions chahiye",
    "bhai health checkup karaya, report aayi hai",
    "arey new hobby shuru karni hai, kya suggest karoge?",
    "tu self improvement ke liye kya kar raha hai?",
    "bhai meditation shuru kiya, mental health important hai",
    "arey daily routine maintain kar raha hoon, disciplined hoon",
    "tu relationships ke baare mein kaisa feel kar raha hai?",
    "bhai life goals set kiye, achieve karne ka plan hai",
    "arey personal finance manage kar raha hoon, savings badhao",
    "tu new skills learn kar raha hai? Online courses dekho",
    "bhai stress management ke tips chahiye, busy life hai",
    "arey work life balance maintain kar raha hoon"
]

all_templates = {
    'family': family_templates,
    'friend_chat': friend_chat_templates,
    'student': student_templates,
    'office': office_templates,
    'delivery': delivery_templates,
    'shopping': shopping_templates,
    'travel': travel_templates,
    'food': food_templates,
    'banking': banking_templates,
    'customer_support': customer_support_templates,
    'cab_service': cab_service_templates,
    'courier': courier_templates,
    'college': college_templates,
    'gaming': gaming_templates,
    'personal': personal_templates
}

def get_language(text):
    hi_count = sum(1 for c in text if ord(c) >= 2304 and ord(c) <= 2416)
    if hi_count > len(text) * 0.3:
        return 'hi'
    elif hi_count > 0:
        return 'hinglish'
    return 'en'

def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def generate_variations(base_text, category, count=50):
    variations = []
    common_prefixes = ["hello", "hi", "hey", "arey", "bhai", "dost", "yaar"]
    common_suffixes = ["?", "!", "yaar", "bhai", "yaar?", "bhai?"]

    for _ in range(count):
        var = base_text
        if random.random() > 0.5 and category not in ['banking', 'office']:
            var = random.choice(common_prefixes) + " " + var
        if random.random() > 0.7:
            var = var + " " + random.choice(common_suffixes)
        var = clean_text(var)
        if var not in [clean_text(t) for t in variations]:
            variations.append(var)
    return variations

def generate_dataset():
    rows = []
    target_per_category = 50

    for category, templates in all_templates.items():
        generated = set()

        for template in templates:
            cleaned = clean_text(template)
            language = get_language(cleaned)
            row = {
                'text': cleaned,
                'label': '0',
                'category': category,
                'language': language,
                'tactics': 'none'
            }
            rows.append(row)
            generated.add(cleaned)

            variations = generate_variations(template, category, 60)
            for var in variations:
                if len(rows) >= 850:
                    break
                if var not in generated:
                    lang = get_language(var)
                    rows.append({
                        'text': var,
                        'label': '0',
                        'category': category,
                        'language': lang,
                        'tactics': 'none'
                    })
                    generated.add(var)

        while len([r for r in rows if r['category'] == category]) < target_per_category:
            template = random.choice(templates)
            cleaned = clean_text(template)
            if cleaned not in generated:
                language = get_language(cleaned)
                rows.append({
                    'text': cleaned,
                    'label': '0',
                    'category': category,
                    'language': language,
                    'tactics': 'none'
                })
                generated.add(cleaned)

    seen = set()
    unique_rows = []
    for row in rows:
        text = row['text']
        if text not in seen:
            seen.add(text)
            unique_rows.append(row)

    final_rows = unique_rows[:850]

    category_counts = {}
    for row in final_rows:
        cat = row['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print(f"Total rows: {len(final_rows)}")
    print("Category distribution:", category_counts)

    return final_rows

if __name__ == "__main__":
    data = generate_dataset()

    with open('./dataset/conversations.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['text', 'label', 'category', 'language', 'tactics'])
        writer.writeheader()
        writer.writerows(data)

    print("Dataset saved to ./dataset/conversations.csv")