const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Footer, AlignmentType,
  HeadingLevel, BorderStyle, WidthType, ShadingType, LevelFormat, PageNumber, PageBreak
} = require('docx');

const ROOT = path.resolve(__dirname, '..');
const T = f => JSON.parse(fs.readFileSync(path.join(ROOT, 'tables', f)));
const L1 = T('level1_results.json'), L2 = T('level2_results.json'), L3 = T('level3_results.json');
const n = x => Number(x).toLocaleString('en-US');
const f2 = x => Number(x).toFixed(2), f3 = x => Number(x).toFixed(3);

const W = 9638; // content width (A4, margins 1134)
const FONT = 'Arial', DARK = '1F3864', GREY = '595959';

const p = (text, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 120, line: 276 }, alignment: o.align,
  children: (Array.isArray(text) ? text : [text]).map(t => typeof t === 'string' ? new TextRun({ text: t, font: FONT, size: o.size ?? 22, color: o.color, bold: o.bold, italics: o.italics }) : t)
});
const b = t => new TextRun({ text: t, bold: true, font: FONT, size: 22 });
const h1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, children: [new TextRun({ text: t, font: FONT })] });
const h2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 }, children: [new TextRun({ text: t, font: FONT })] });
const h3 = t => new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 160, after: 80 }, children: [new TextRun({ text: t, font: FONT })] });
const bullets = arr => arr.map(t => new Paragraph({ numbering: { reference: 'bul', level: 0 }, spacing: { after: 60, line: 276 },
  children: (Array.isArray(t) ? t : [t]).map(x => typeof x === 'string' ? new TextRun({ text: x, font: FONT, size: 22 }) : x) }));
const pb = () => new Paragraph({ children: [new PageBreak()] });

// callout box (single-cell shaded table)
const note = (label, text, fill = 'EAF1FB') => new Table({
  width: { size: W, type: WidthType.DXA }, columnWidths: [W],
  rows: [new TableRow({ children: [new TableCell({
    width: { size: W, type: WidthType.DXA }, shading: { fill, type: ShadingType.CLEAR },
    margins: { top: 100, bottom: 100, left: 160, right: 160 },
    borders: { top: { style: BorderStyle.SINGLE, size: 1, color: 'BBBBBB' }, bottom: { style: BorderStyle.SINGLE, size: 1, color: 'BBBBBB' }, left: { style: BorderStyle.SINGLE, size: 18, color: DARK }, right: { style: BorderStyle.SINGLE, size: 1, color: 'BBBBBB' } },
    children: [new Paragraph({ spacing: { after: 0, line: 270 }, children: [new TextRun({ text: label + ' ', bold: true, font: FONT, size: 21 }), new TextRun({ text, font: FONT, size: 21 })] })]
  })] })]
});
const gap = () => new Paragraph({ spacing: { after: 100 }, children: [] });

function table(headers, rows, widths, opts = {}) {
  const tot = widths.reduce((a, c) => a + c, 0);
  const bd = { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' };
  const borders = { top: bd, bottom: bd, left: bd, right: bd };
  const cell = (t, w, hdr, i) => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders,
    shading: hdr ? { fill: DARK, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ alignment: (i === 0 || opts.leftCols?.includes(i)) ? AlignmentType.LEFT : AlignmentType.RIGHT, spacing: { after: 0 },
      children: [new TextRun({ text: String(t), font: FONT, size: 19, bold: hdr, color: hdr ? 'FFFFFF' : undefined })] })]
  });
  return new Table({ width: { size: tot, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], true, i)) }),
      ...rows.map(r => new TableRow({ children: r.map((c, i) => cell(c, widths[i], false, i)) }))] });
}

function pngSize(file) { const buf = fs.readFileSync(file); return [buf.readUInt32BE(16), buf.readUInt32BE(20)]; }
function img(name, caption, wpx = 610) {
  const file = path.join(ROOT, 'charts', name); const [w, h] = pngSize(file);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, keepNext: true,
      children: [new ImageRun({ type: 'png', data: fs.readFileSync(file), transformation: { width: wpx, height: Math.round(wpx * h / w) },
        altText: { title: caption, description: caption, name } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: caption, italics: true, font: FONT, size: 18, color: GREY })] })
  ];
}
const cap = t => new Paragraph({ spacing: { before: 120, after: 60 }, keepNext: true, children: [new TextRun({ text: t, bold: true, font: FONT, size: 20, color: DARK })] });

const kids = [];
const add = (...x) => x.flat().forEach(e => kids.push(e));

// ---------------- 1. TITLE PAGE ----------------
add(
  new Paragraph({ spacing: { before: 1800, after: 200 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'COGNIFYZ TECHNOLOGIES', bold: true, font: FONT, size: 32, color: GREY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 }, children: [new TextRun({ text: 'Data Analysis Internship', font: FONT, size: 26, color: GREY })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: DARK, space: 12 } },
    children: [new TextRun({ text: 'Restaurant Data Analysis', bold: true, font: FONT, size: 56, color: DARK })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 1200 }, children: [new TextRun({ text: 'Internship Project Report: Levels 1, 2 and 3', font: FONT, size: 28 })] }),
  p([b('Prepared by: '), 'Chowduru Nandeeswar Reddy'], { align: AlignmentType.CENTER, after: 60 }),
  p('Department of Electronics and Communication Engineering', { align: AlignmentType.CENTER, after: 60 }),
  p('Sathyabama Institute of Science and Technology', { align: AlignmentType.CENTER, after: 60 }),
  p([b('Dataset: '), '9,551 restaurants, 21 columns (Dataset .csv)'], { align: AlignmentType.CENTER, after: 60 }),
  p([b('Tools: '), 'Python, pandas, NumPy, Matplotlib, Seaborn, SciPy, Folium'], { align: AlignmentType.CENTER, after: 60 }),
  p([b('Date: '), 'October 2026'], { align: AlignmentType.CENTER }),
  pb()
);

// ---------------- 2. OVERVIEW ----------------
add(h1('1. Project Overview'),
  p('This report presents the work done for the Cognifyz Technologies Data Analysis Internship. The internship task list contains three levels, and an intern must complete any two. This project completes all three levels so that every task the dataset can support is covered. Every number in this report was calculated from the supplied restaurant dataset using the Python scripts delivered with the report.'),
  p('The dataset describes 9,551 restaurants. Each row holds the restaurant name, location, cuisines, price range, online delivery and table booking availability, aggregate rating and number of votes.'),
  note('Tasks not fully supported:', 'Level 3, Task 1 (Restaurant Reviews) asks for analysis of written review text. The dataset has no review text column, so keyword analysis and review length cannot be calculated. This is explained in Section 8.3 instead of using invented results. All other tasks (11 of 12) were completed.', 'FFF4E5'),
  gap(),
  h1('2. Objectives'),
  ...bullets([
    'Level 1: find the most common cuisines, compare cities, study price ranges and measure online delivery.',
    'Level 2: study the rating distribution and votes, cuisine combinations, geographic spread and restaurant chains.',
    'Level 3: study votes against ratings, and price range against online delivery and table booking.',
    'Show a clear method, state every assumption and report limitations honestly.'
  ]));

// ---------------- 3. DATASET ----------------
add(h1('3. Dataset Description'),
  p('The file contains 9,551 rows and 21 columns. Each row is one restaurant, and no Restaurant ID is repeated. The columns used in this project are listed below.'),
  table(['Column', 'Meaning', 'Used for'], [
    ['Restaurant Name', 'Name of the restaurant', 'Chains'],
    ['City, Locality, Country Code', 'Where the restaurant is', 'City and geographic tasks'],
    ['Longitude, Latitude', 'Map coordinates', 'Geographic analysis'],
    ['Cuisines', 'Comma-separated list of cuisines', 'Top cuisines, combinations'],
    ['Price range', 'Category from 1 (lowest) to 4 (highest)', 'Price tasks'],
    ['Has Online delivery, Has Table booking', 'Yes / No', 'Delivery and booking tasks'],
    ['Aggregate rating', 'Score from 0 to 5 (0 = not rated)', 'All rating tasks'],
    ['Votes', 'Number of votes received', 'Votes tasks'],
    ['Rating text', 'Six fixed labels (Excellent, Very Good, Good, Average, Poor, Not rated)', 'Review task check']
  ], [2900, 4338, 2400], { leftCols: [1, 2] }),
  gap(),
  p('Key facts about the data, all calculated from the file:'),
  ...bullets([
    '9,551 restaurants in 141 cities and 15 country codes. Country code 1 (India) holds 8,652 restaurants (90.6%), and New Delhi alone holds 5,473 (57.3%).',
    'The only column with missing values is Cuisines (9 blank entries). There are no duplicate rows.',
    `${n(L1.rated_restaurants)} restaurants have a real rating. ${n(L1.unrated_restaurants)} restaurants (22.5%) have Aggregate rating = 0 and Rating text = "Not rated".`,
    '145 different cuisine names appear in the file.'
  ]),
  h1('4. Data Cleaning and Preprocessing'),
  ...bullets([
    [b('Unrated restaurants. '), `The ${n(L1.unrated_restaurants)} rows with rating 0 mean "no rating", not a score of zero. They are excluded from every average rating and kept in counts and percentages. These rows have 0 to 3 votes each.`],
    [b('Missing cuisines. '), 'The 9 restaurants with blank Cuisines are left out of cuisine tasks only. Cuisine percentages use 9,542 as the denominator.'],
    [b('Invalid coordinates. '), '497 restaurants have Longitude = 0 and Latitude = 0, which is a placeholder, not a real location (495 of them are in India). They are removed from maps only. 9,054 restaurants are plotted.'],
    [b('Multi-cuisine restaurants. '), 'A restaurant listing several cuisines is counted once under each cuisine (so cuisine percentages add to more than 100%). Duplicate cuisine names inside one row are counted once.'],
    [b('Text encoding. '), 'A few city names contain damaged characters (for example Sao Paulo). This does not change any result.'],
    [b('Column names. '), 'Spaces around column names are trimmed when the file is loaded.']
  ]),
  h1('5. Methodology'),
  ...bullets([
    'Data was loaded with pandas and summarised with groupby, value_counts and crosstab.',
    'Percentages always use the stated group size as the denominator (for example, all 9,551 restaurants, or only the restaurants in one price range).',
    'Averages of ratings use rated restaurants only. Where a group is small, the group size (n) is shown next to the average.',
    'Correlation uses Spearman rank correlation (main measure) and Pearson correlation, calculated with SciPy.',
    'A chi-square test checks whether differences between price ranges are larger than chance.',
    'Charts were drawn with Matplotlib and Seaborn. The interactive map was built with Folium.',
    'All rounded numbers are rounded half-up once, from the unrounded value (for example 4.475 becomes 4.48), so tables, text, charts and files agree.',
    'Correlation is never treated as proof of cause.'
  ]),
  pb());

// ---------------- 6. LEVEL 1 ----------------
add(h1('6. Level 1 Analysis'));
// L1T1
add(h2('6.1 Task 1: Top Cuisines'),
  p('Goal: find the three most common cuisines and the percentage of restaurants serving each. Denominator: 9,542 restaurants with cuisine information.'),
  cap('Table 1: Top 10 cuisines'),
  table(['Rank', 'Cuisine', 'Restaurants', '% of 9,542'], L1.t1_top10.map((r, i) => [i + 1, r.Cuisine, n(r.Restaurants), f2(r.Percentage) + '%']), [1000, 3638, 2500, 2500], { leftCols: [1] }),
  gap(),
  ...img('l1t1_top_cuisines.png', 'Figure 1: Top 10 cuisines by number of restaurants (top 3 highlighted)', 560),
  p([b('Result. '), 'The top three cuisines are North Indian (3,960 restaurants, 41.50%), Chinese (2,733, 28.64%) and Fast Food (1,986, 20.81%).']),
  p([b('Interpretation. '), 'North Indian food is served by about two out of every five restaurants. The percentages add to more than 100% because many restaurants offer more than one cuisine. The ranking reflects the dataset, which is mostly Delhi NCR.']));
// L1T2
const c5 = L1.t2_top5_by_count;
add(h2('6.2 Task 2: City Analysis'),
  p('Goal: find the city with the most restaurants, the average rating of each city, and the city with the highest average rating.'),
  cap('Table 2: Five cities with the most restaurants'),
  table(['City', 'Restaurants', 'Rated restaurants', 'Average rating'], c5.map(r => [r.City, n(r.Restaurants), n(r.Rated_Restaurants), f2(r.Avg_Rating)]), [3038, 2200, 2200, 2200]),
  gap(),
  ...img('l1t2_restaurants_by_city.png', 'Figure 2: Top 10 cities by number of restaurants', 520),
  p([b('Most restaurants. '), 'New Delhi has 5,473 restaurants, which is 57.30% of the whole dataset. It is followed by Gurgaon (1,118) and Noida (1,080).']),
  p([b('Highest average rating, two ways. '), 'Without any sample-size rule, the highest averages belong to tiny cities: Inner City (4.90, only 2 restaurants), Quezon City (4.80, 1 restaurant), Makati City (4.65, 2 restaurants). These are misleading. 46 of the 141 cities have one or no rated restaurant.']),
  cap('Table 3: Highest average rating among cities with at least 20 rated restaurants (71 cities qualify)'),
  table(['Rank', 'City', 'Rated restaurants (n)', 'Average rating'], L1.t2_fair_best_top5.map((r, i) => [i + 1, r.City, r.Rated_Restaurants, f2(r.Avg_Rating)]), [1000, 3638, 2500, 2500], { leftCols: [1] }),
  gap(),
  ...img('l1t2_avg_rating_by_city.png', 'Figure 3: Top 10 cities by average rating (minimum 20 rated restaurants)', 520),
  p([b('Result. '), 'With a minimum of 20 rated restaurants, London has the highest average rating (4.54), followed by Orlando (4.48). Tampa Bay and Rest of Hawaii are tied at 4.41. The large Delhi NCR cities are lower: New Delhi 3.30, Gurgaon 3.33 and Noida 3.16.']),
  p([b('Caution. '), '67 of the 141 cities have exactly 20 restaurants in the file, and even 20 is a small sample. The city ranking is a description of this dataset, not proof that one city is better than another.']));
// L1T3
add(h2('6.3 Task 3: Price Range Distribution'),
  p('Goal: show the distribution of price ranges and the percentage in each. Denominator: all 9,551 restaurants (no missing values).'),
  cap('Table 4: Price range distribution'),
  table(['Price range', 'Restaurants', 'Percentage'], L1.t3_price.map(r => [r['Price range'], n(r.Restaurants), f2(r.Percentage) + '%']), [3038, 3300, 3300]),
  gap(),
  ...img('l1t3_price_range.png', 'Figure 4: Number of restaurants in each price range', 440),
  p([b('Result. '), 'Price range 1 is the largest group (46.53%), followed by range 2 (32.59%), range 3 (14.74%) and range 4 (6.14%).']),
  p([b('Interpretation. '), 'Almost four out of five restaurants (79.12%) are in the two lowest price ranges. The number of restaurants falls steadily as price range rises. The dataset does not explain how the ranges are defined, and costs are recorded in different currencies, so the range is used only as an ordered category.']));
// L1T4
const t4 = L1.t4;
add(h2('6.4 Task 4: Online Delivery'),
  p('Goal: find the percentage of restaurants offering online delivery and compare average ratings with and without it.'),
  cap('Table 5: Online delivery and average rating'),
  table(['Group', 'Restaurants', '% of 9,551', 'Rated restaurants', 'Average rating', 'Median'], [
    ['With online delivery', n(t4.yes), f2(t4.yes_pct) + '%', n(t4.n_yes_rated), f2(t4.avg_yes), t4.median_yes],
    ['Without online delivery', n(t4.no), f2(100 - t4.yes_pct) + '%', n(t4.n_no_rated), f2(t4.avg_no), t4.median_no]
  ], [2638, 1400, 1300, 1700, 1500, 1100]),
  gap(),
  ...img('l1t4_online_delivery.png', 'Figure 5: Average rating by online delivery and share of restaurants offering it', 580),
  p([b('Result. '), '2,451 of 9,551 restaurants (25.66%) offer online delivery. Among rated restaurants, those with delivery average 3.38 and those without average 3.47, a difference of 0.09. Both groups have a median of 3.4.']),
  note('Important method point:', 'Only 3.92% of restaurants with delivery are unrated, but 28.90% of restaurants without delivery are unrated. If the unrated zeros were wrongly included, the averages would be 3.25 (with delivery) and 2.47 (without), which would falsely suggest delivery restaurants rate much higher. This is why unrated restaurants are excluded from averages.', 'FFF4E5'),
  gap(),
  p([b('Interpretation. '), 'Restaurants with and without online delivery have very similar ratings; the small gap is not a reason to say delivery changes ratings. Inside each price range the direction of the gap changes (delivery is slightly higher in ranges 1 and 4, lower in ranges 2 and 3), so the data show no consistent link. No cause-and-effect claim can be made from this comparison.']),
  pb());

// ---------------- 7. LEVEL 2 ----------------
const t1 = L2.t1;
add(h1('7. Level 2 Analysis'));
add(h2('7.1 Task 1: Restaurant Ratings'),
  p('Goal: describe the distribution of aggregate ratings, find the most common rating range and calculate the average number of votes.'),
  p([b('Handling of unrated restaurants. '), '2,148 restaurants have rating 0 ("Not rated"). They are excluded from the rating distribution, which therefore describes the 7,403 rated restaurants. The lowest real rating is 1.8 and the highest is 4.9.']),
  cap('Table 6: Distribution of ratings (rated restaurants, bins of 0.5)'),
  table(['Rating range', 'Restaurants', '% of 7,403 rated'], t1.ranges.map(r => [r['Rating range'], n(r.Restaurants), f2(r['Percent of rated']) + '%']), [3038, 3300, 3300]),
  gap(),
  ...img('l2t1_rating_distribution.png', 'Figure 6: Distribution of aggregate ratings', 520),
  p([b('Result. '), 'The most common rating range is 3.0 to 3.4, with 2,490 restaurants (33.64% of rated restaurants). The ranges 3.0 to 3.9 together hold 62.0%. The single most common exact rating is 3.2 (522 restaurants). The mean rating is 3.44 and the median is 3.4.']),
  p([b('Votes. '), 'The average number of votes is 156.91 per restaurant across all 9,551 restaurants, and 202.19 across the 7,403 rated restaurants. The median is only 31 votes (60 for rated restaurants), because a few very popular restaurants pull the average up. The maximum is 10,934 votes.']),
  p([b('Interpretation. '), 'Ratings are centred on the middle: few restaurants are below 2.5 (2.5% of rated) or above 4.5 (4.1% of rated). Most restaurants receive few votes, and a small number receive thousands, so the median describes a typical restaurant better than the mean.']));

const cm = L2.t2;
add(h2('7.2 Task 2: Cuisine Combination'),
  p('Goal: find the most common cuisine combinations and whether some combinations have higher ratings.'),
  p([b('Method. '), `A combination is the full set of cuisines a restaurant lists, sorted alphabetically so that order does not matter. Only restaurants with two or more cuisines are treated as combinations (${n(cm.n_multi)} restaurants; ${n(cm.n_single)} list a single cuisine). There are ${n(cm.n_combos_total)} different combinations. Average ratings use rated restaurants only.`]),
  cap('Table 7: Ten most common cuisine combinations'),
  table(['Combination', 'Restaurants', 'Rated', 'Average rating'], cm.most_common.map(r => [r.Combination, n(r.Restaurants), r.Rated, f2(r.Avg_Rating)]), [4638, 1600, 1500, 1900], { leftCols: [0] }),
  gap(),
  p([b('Threshold. '), `Averages from very few restaurants are unreliable, so a combination is compared only if it has at least ${cm.min_threshold} rated restaurants. This is a judgement rule: it keeps the comparison fair and still leaves ${cm.n_combos_min20} combinations to compare. The average of all multi-cuisine restaurants is ${f2(cm.overall_avg_multi)}.`]),
  cap('Table 8: Highest-rated and lowest-rated combinations (minimum 20 rated restaurants)'),
  table(['Combination', 'Rated (n)', 'Average rating'], [...cm.best.slice(0, 6), ...cm.worst].map(r => [r.Combination, r.Rated, f2(r.Avg_Rating)]), [5638, 1800, 2200], { leftCols: [0] }),
  gap(),
  ...img('l2t2_cuisine_combinations.png', 'Figure 7: Most common combinations (left) and highest-rated combinations (right)', 620),
  p([b('Result. '), 'The most common combination is Chinese + North Indian (616 restaurants), then Mughlai + North Indian (395) and Chinese + Mughlai + North Indian (306). The common combinations have average ratings of about 3.0 to 3.4, close to the overall average of 3.45. The highest averages are Japanese + Sushi (4.06, n = 20), Italian + Pizza (3.74, n = 42) and Continental + Italian + North Indian (3.68, n = 29). The lowest are Fast Food + Raw Meats (2.99), American + Fast Food + Healthy Food + Salad (3.00) and Fast Food + Pizza (3.03).']),
  p([b('Interpretation. '), 'Combinations that include Italian, Continental or Japanese cuisine tend to have higher ratings, while fast-food-based combinations tend to have lower ratings. The differences are real in this data but modest, and the Japanese + Sushi result rests on exactly 20 restaurants spread over several countries. Location and price level are not controlled, so these are patterns, not rules.']));

const g = L2.t3;
add(h2('7.3 Task 3: Geographic Analysis'),
  p('Goal: plot restaurant locations using longitude and latitude and describe any clusters.'),
  p(`497 restaurants have placeholder coordinates (0, 0) and were removed, leaving ${n(g.plotted)} plotted restaurants.`),
  ...img('l2t3_geo_world.png', 'Figure 8: Restaurant locations in the dataset (longitude and latitude)', 560),
  ...img('l2t3_geo_ncr_density.png', 'Figure 9: Delhi NCR locations (left) and density of restaurants (right)', 620),
  cap('Table 9: Ten localities with the most restaurants'),
  table(['Locality', 'City', 'Restaurants'], g.top_localities.map(r => [r.Locality, r.City, r.Restaurants]), [4038, 3200, 2400], { leftCols: [1] }),
  gap(),
  p([b('Result. '), `${f2(g.india_pct)}% of the plotted restaurants are in India, and ${n(g.ncr_points)} (${f2(g.ncr_pct)}%) lie inside the Delhi NCR area (latitude 28.2 to 28.95, longitude 76.8 to 77.7). The remaining plotted points are other Indian cities (608 restaurants) and small groups in other countries (the currencies in the file suggest the USA, UK, UAE, Brazil, South Africa and others), so the world map shows one dense mass in North India and scattered points elsewhere.`]),
  p([b('Clusters. '), 'Inside Delhi NCR the restaurants form several clusters: central Delhi, west and north Delhi, south Delhi, Noida, Gurgaon and Faridabad. The densest areas are central Delhi (a grid cell near latitude 28.63, longitude 77.22 holds 147 restaurants; Connaught Place is the largest locality with 122) and Noida (cells near 28.57, 77.32 hold 104 and 79 restaurants; Sector 18 has 75).']),
  p([b('Interactive map. '), 'The file l2t3_restaurant_map.html (opens in any browser) shows a density heat map and clustered markers for a sample of 1,500 Delhi NCR restaurants.']),
  note('Limitation:', 'Because the dataset is mostly Delhi NCR, it cannot show worldwide restaurant patterns. The clusters show where restaurants were collected in this dataset, which may not equal where restaurants exist in real life.'));

const c4 = L2.t4;
add(h2('7.4 Task 4: Restaurant Chains'),
  p('Goal: identify restaurant chains and analyse their ratings and popularity.'),
  p([b('Method. '), `A chain is a restaurant name that appears at two or more rows in the dataset. Each row is counted as one outlet. By this rule, ${n(c4.n_chain_names)} names are chains, covering ${n(c4.chain_outlets)} restaurants (${f2(c4.chain_outlets_pct)}% of the dataset). Because the rule uses names only, two unrelated restaurants with the same name would be counted as one chain.`]),
  p([b('Ranking criteria. '), 'Chains are ranked by number of outlets; ties are broken by total votes. Popularity is shown by total votes and quality by average rating (rated outlets only).']),
  cap('Table 10: Top 10 chains by number of outlets'),
  table(['Chain', 'Outlets', 'Cities', 'Avg rating', 'Total votes'], c4.top10.map(r => [r['Restaurant Name'], r.Outlets, r.Cities, f2(r.Avg_Rating), n(r.Total_Votes)]), [3238, 1400, 1400, 1800, 1800], { leftCols: [] }),
  gap(),
  ...img('l2t4_restaurant_chains.png', 'Figure 10: Top 10 chains: outlets, average rating and total votes', 620),
  cap('Table 11: Chains with at least 10 rated outlets (36 chains): highest and lowest average rating'),
  table(['Chain', 'Outlets', 'Avg rating', 'Total votes'], [...c4.best_min10.slice(0, 3), ...c4.worst_min10].map(r => [r['Restaurant Name'], r.Outlets, f2(r.Avg_Rating), n(r.Total_Votes)]), [3838, 1800, 2000, 2000]),
  gap(),
  p([b('Result. '), 'Cafe Coffee Day has the most outlets (83), followed by Domino\'s Pizza (79), Subway (63), Green Chick Chop (51) and McDonald\'s (48). Barbeque Nation is the clear leader in popularity and quality: 26 outlets in 22 cities, an average rating of 4.35 and 28,142 total votes, far more than any other chain. Among chains with at least 10 rated outlets, Starbucks (3.81) and Chaayos (3.75) follow it, and Wah Ji Wah (2.62), Chicago Pizza (2.79) and Pizza Hut Delivery (2.81) are lowest.']),
  p([b('Interpretation. '), `The biggest chains by outlets are mostly fast-food and cafe chains, and their average ratings (about 2.9 to 3.4) are close to or below the dataset average of 3.44. Chain restaurants overall average ${f2(c4.chain_avg)}, slightly below non-chain names (${f2(c4.non_chain_avg)}). Size therefore does not guarantee a high rating. Chains with fewer, more upscale outlets, such as Barbeque Nation and AB's - Absolute Barbecues, have the highest ratings and votes per outlet.`]),
  pb());

// ---------------- 8. LEVEL 3 ----------------
const v = L3.t2, s = L3.t3;
add(h1('8. Level 3 Analysis'));
add(h2('8.1 Task 2: Votes Analysis'),
  p('Goal: find the restaurants with the most and fewest votes and analyse the relationship between votes and rating.'),
  cap('Table 12: Ten restaurants with the most votes'),
  table(['Restaurant', 'City', 'Votes', 'Rating'], v.top10.map(r => [r['Restaurant Name'], r.City, n(r.Votes), r['Aggregate rating']]), [3638, 2200, 1900, 1900], { leftCols: [1] }),
  gap(),
  p([b('Highest votes. '), 'Toit in Bangalore has the most votes (10,934, rating 4.8), followed by Truffles in Bangalore (9,667) and Hauz Khas Social in New Delhi (7,931). Bangalore restaurants hold five of the top ten places.']),
  p([b('Lowest votes. '), `${n(v.zero_votes)} restaurants (${f2(v.zero_votes_pct)}%) have 0 votes, so many restaurants tie for the lowest. All of them are also unrated. Among restaurants that have a rating, the lowest vote count is ${v.min_votes_rated} (${v.n_min_votes_rated} restaurants).`]),
  p([b('Correlation method. '), `Unrated restaurants (rating 0) are excluded because 0 is not a real score, leaving ${n(v.n)} restaurants. Spearman rank correlation is the main measure because votes are heavily skewed. Pearson correlation is shown for comparison.`]),
  cap('Table 13: Correlation between votes and aggregate rating (rated restaurants)'),
  table(['Measure', 'Value'], [['Spearman rank correlation', f2(v.spearman)], ['Pearson correlation (votes)', f2(v.pearson)], ['Pearson correlation (log of votes + 1)', f2(v.pearson_log)]], [6638, 3000]),
  gap(),
  cap('Table 14: Average rating by number of votes (rated restaurants)'),
  table(['Votes received', 'Restaurants', 'Average rating'], v.vote_group.map(r => [r['Vote group'], n(r['count']), f2(r.mean)]), [3638, 3000, 3000]),
  gap(),
  ...img('l3t2_votes_vs_rating.png', 'Figure 11: Votes (log scale) against rating, and average rating by vote group', 620),
  p([b('Interpretation in simple English. '), 'Restaurants with more votes usually have higher ratings. The Spearman value of 0.68 is a moderate to strong positive relationship, and the table shows the average rating rising step by step from 2.98 (up to 10 votes) to 4.20 (over 1,000 votes). The Pearson value (0.41) is lower because a few restaurants have extremely high vote counts; the relationship is clearer when votes are put on a log scale (0.65).']),
  note('Careful reading:', 'This is a correlation, not proof of cause. Highly rated restaurants may attract more customers and so collect more votes, or popular restaurants may be rated more generously, or both may reflect location and price. If the unrated zeros were included, the Spearman value would rise to 0.85, but that increase is an artefact of the placeholder zeros, so it is not used.', 'FFF4E5'),
  gap());

add(h2('8.2 Task 3: Price Range vs Online Delivery and Table Booking'),
  p('Goal: analyse whether online delivery and table booking depend on price range, and whether higher-priced restaurants are more likely to offer them. Each percentage uses the number of restaurants in that price range as the denominator.'),
  cap('Table 15: Online delivery by price range'),
  table(['Price range', 'Restaurants', 'With delivery', 'Without delivery', '% with delivery'], s.delivery.map(r => [r['Price range'], n(r.Total), n(r['Delivery Yes']), n(r['Delivery No']), f2(r['Delivery Yes %']) + '%']), [1800, 1900, 1900, 2038, 2000]),
  gap(),
  cap('Table 16: Table booking by price range'),
  table(['Price range', 'Restaurants', 'With booking', 'Without booking', '% with booking'], s.booking.map(r => [r['Price range'], n(r.Total), n(r['Booking Yes']), n(r['Booking No']), f2(r['Booking Yes %']) + '%']), [1800, 1900, 1900, 2038, 2000]),
  gap(),
  ...img('l3t3_price_vs_services.png', 'Figure 12: Share of restaurants offering online delivery and table booking, by price range', 620),
  p([b('Table booking. '), 'Table booking rises sharply with price. It is almost absent in price range 1 (1 restaurant, 0.02%), rare in range 2 (7.68%) and common in ranges 3 (45.74%) and 4 (46.76%). The Spearman correlation is 0.47, and the chi-square test shows the differences are far larger than chance (p < 0.001). Higher-priced restaurants are clearly more likely to offer table booking.']),
  p([b('Online delivery. '), 'Online delivery does not rise steadily with price. It peaks in price range 2 (41.31%), is 29.19% in range 3, 15.77% in range 1 and lowest in range 4 (9.04%). The relationship is statistically significant (p < 0.001) but weak overall (Spearman 0.14) and not in one direction. Higher-priced restaurants are not more likely to offer online delivery; the top range is the least likely.']),
  p([b('Check on India only. '), 'Because price range may mean different things in different countries, the calculation was repeated for the 8,652 Indian restaurants. The pattern is the same: table booking is 0.02%, 8.22%, 56.17% and 64.69% for ranges 1 to 4, and delivery is 16.32%, 44.82%, 35.82% and 11.08%.']),
  p([b('Interpretation. '), 'Table booking is a feature of mid-to-high priced dining, where customers plan a visit. Online delivery is most common among mid-priced restaurants, which suggests a delivery-friendly format rather than a price effect. Again, these are associations in this dataset.']));

add(h2('8.3 Task 1: Restaurant Reviews (Not Supported by This Dataset)'),
  p('This task asks for the most common positive and negative keywords in written reviews, the average review length and its relationship with rating.'),
  p('The dataset was checked column by column. None of the 21 columns holds customer review text. The only text-like column, Rating text, contains six fixed labels (Average, Not rated, Good, Very Good, Excellent, Poor), the longest being 9 characters. These labels are just the rating score written in words, so they are not reviews.'),
  note('Conclusion:', 'Keyword analysis, average review length and review length versus rating cannot be calculated from the supplied files. No results are reported for this task rather than presenting rating labels as reviews. To complete it, a dataset with a review text column would be needed.', 'FFF4E5'),
  pb());

// ---------------- 9. KEY FINDINGS ----------------
add(h1('9. Key Findings'),
  ...bullets([
    'North Indian (41.50%), Chinese (28.64%) and Fast Food (20.81%) are the three most common cuisines.',
    'New Delhi has the most restaurants (5,473; 57.30% of the data). Among cities with at least 20 rated restaurants, London has the highest average rating (4.54).',
    'Prices are concentrated at the low end: 79.12% of restaurants are in price ranges 1 and 2.',
    '25.66% of restaurants offer online delivery. Rated restaurants with and without delivery average 3.38 and 3.47, so there is no meaningful rating advantage either way.',
    'The most common rating range is 3.0 to 3.4 (33.64% of rated restaurants). The average is 156.91 votes per restaurant, but the median is only 31.',
    'Chinese + North Indian is the most common cuisine combination (616 restaurants). Combinations with Italian, Continental or Japanese cuisine rate higher; fast-food combinations rate lower.',
    '83.38% of the plotted restaurants lie in Delhi NCR, with the densest clusters in central Delhi (Connaught Place) and Noida.',
    'Cafe Coffee Day, Domino\'s Pizza and Subway have the most outlets, but Barbeque Nation stands out with a 4.35 average rating and 28,142 votes.',
    'Votes and ratings are positively related (Spearman 0.68): restaurants with more votes tend to have higher ratings.',
    'Table booking increases strongly with price range (0.02% to 46.76%). Online delivery peaks at price range 2 (41.31%) and is lowest at range 4 (9.04%).'
  ]),
  h1('10. Limitations'),
  ...bullets([
    [b('Location bias. '), '90.6% of restaurants are in India and 57.3% in New Delhi, so the results mainly describe Delhi NCR, not restaurants worldwide.'],
    [b('Unrated restaurants. '), '22.5% of restaurants have no rating and are excluded from average ratings, which may bias averages if unrated restaurants differ from rated ones.'],
    [b('Small samples. '), '67 cities have exactly 20 restaurants, and some combinations and chains rest on few restaurants. Thresholds (20 rated restaurants for cities and combinations, 10 rated outlets for chains) are judgement choices.'],
    [b('Chains by name. '), 'Chains are identified by identical names, so unrelated restaurants with the same name, or the same chain under different spellings (for example Pizza Hut and Pizza Hut Delivery), are not handled perfectly.'],
    [b('Price range. '), 'The dataset does not define the price ranges, and costs are in different currencies, so the ranges are treated only as ordered categories.'],
    [b('Coordinates. '), '497 restaurants have placeholder coordinates and are missing from maps.'],
    [b('No review text. '), 'Level 3 Task 1 cannot be answered from this dataset.'],
    [b('Association only. '), 'Differences between groups are associations; the data cannot show cause and effect. Ratings and votes are also a single snapshot with no dates.']
  ]),
  h1('11. Conclusion'),
  p('This project analysed 9,551 restaurant records to complete eleven of the twelve tasks in the three levels of the Cognifyz Data Analysis Internship. The twelfth task needs review text that the dataset does not contain, and this is clearly stated instead of being filled with invented results.'),
  p('The analysis shows a dataset dominated by Delhi NCR, where North Indian and Chinese food are the most common cuisines and most restaurants are low or mid priced. Ratings cluster around 3.4, most restaurants have few votes, and a small group of popular restaurants receive thousands. Restaurants with more votes tend to be rated higher, and table booking is strongly linked to higher price range, while online delivery is not.'),
  p('The project also shows why careful handling matters: leaving out unrated restaurants, using sample-size thresholds, and choosing the correct denominator all change the conclusions. All code, tables and charts are provided so that every number can be reproduced.'),
  h1('Appendix: How to Reproduce the Results'),
  ...bullets([
    'Install Python 3.9 or newer. In a terminal run: pip install pandas numpy matplotlib seaborn scipy folium',
    'Keep the folder structure: code/, data/ (put Dataset .csv here), charts/ and tables/.',
    'VS Code: open the folder, open code/level1_analysis.py and click Run (or run python level1_analysis.py in the terminal from the code folder). Repeat for level2 and level3.',
    'Jupyter Notebook: each script is split into cells with "# %%" markers. VS Code runs them as interactive cells; in Jupyter, copy each section into its own notebook cell.',
    'Charts are saved to charts/, tables to tables/, and the interactive map to charts/l2t3_restaurant_map.html.',
    'Run python verify_results.py last. It recalculates the key results independently from the raw CSV and reports OK or MISMATCH for each one.'
  ]));

const doc = new Document({
  creator: 'Internship Report', title: 'Cognifyz Data Analysis Internship Report',
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 32, bold: true, font: FONT, color: DARK }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 26, bold: true, font: FONT, color: '2E5C9A' }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 23, bold: true, font: FONT }, paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 2 } }
    ]
  },
  numbering: { config: [{ reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '\u2022', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'Cognifyz Data Analysis Internship | Page ', font: FONT, size: 18, color: GREY }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: GREY })] })] }) },
    children: kids
  }]
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(path.join(ROOT, 'report', 'Cognifyz_Internship_Report.docx'), buf); console.log('saved'); });
