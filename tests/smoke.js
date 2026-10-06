import http from 'k6/http';
import { check, sleep } from 'k6';

const baseUrl = __ENV.BASE_URL;
const token = __ENV.DEMO_TOKEN;
if (baseUrl !== 'https://quickpizza.grafana.com' || !token) {
  throw new Error('Load BASE_URL and DEMO_TOKEN from .env.example. This smoke targets the hosted QuickPizza demo.');
}

export const options = {
  scenarios: { smoke: { executor: 'shared-iterations', vus: 1, iterations: 3, maxDuration: '2m' } },
  maxRedirects: 0,
  thresholds: {
    checks: ['rate==1'],
    http_req_failed: ['rate==0'],
    http_reqs: ['count==9'],
    iterations: ['count==3'],
    'http_req_duration{operation:vegetarian}': ['max<3000'],
    'http_req_duration{operation:restricted}': ['max<3000'],
    'http_req_duration{operation:unauthorized}': ['max<3000'],
  },
};

function json(response) {
  try { return response.json(); } catch { return null; }
}

function recommend(operation, restrictions) {
  const response = http.post(`${baseUrl}/api/pizza`, JSON.stringify(restrictions), {
    headers: { 'Content-Type': 'application/json', Authorization: `token ${token}` },
    tags: { operation }, timeout: '10s',
    responseCallback: http.expectedStatuses(200),
  });
  const body = json(response);
  check(response, {
    [`${operation}: HTTP 200`]: r => r.status === 200,
    [`${operation}: JSON content type`]: r => (r.headers['Content-Type'] || '').includes('application/json'),
    [`${operation}: pizza identity`]: () => Number.isInteger(body?.pizza?.id) && body.pizza.id > 0 && typeof body.pizza.name === 'string' && body.pizza.name.length > 0,
    [`${operation}: ingredients contract`]: () => Array.isArray(body?.pizza?.ingredients) && body.pizza.ingredients.length > 0 && body.pizza.ingredients.every(i => typeof i.name === 'string' && typeof i.vegetarian === 'boolean' && Number.isFinite(i.caloriesPerSlice)),
    [`${operation}: restrictions respected`]: () => Number.isFinite(body?.calories) && body.calories > 0 && body.calories <= restrictions.maxCaloriesPerSlice &&
      (!restrictions.mustBeVegetarian || (body.vegetarian === true && body.pizza?.ingredients?.every(i => i.vegetarian === true))) &&
      typeof body?.pizza?.tool === 'string' && !restrictions.excludedTools.includes(body.pizza.tool) &&
      Array.isArray(body?.pizza?.ingredients) && body.pizza.ingredients.every(i => !restrictions.excludedIngredients.includes(i.name)),
  });
}

export default function () {
  recommend('vegetarian', { maxCaloriesPerSlice: 500, mustBeVegetarian: true, excludedIngredients: [], excludedTools: [], minNumberOfToppings: 2, maxNumberOfToppings: 6 });
  sleep(1);
  recommend('restricted', { maxCaloriesPerSlice: 500, mustBeVegetarian: false, excludedIngredients: ['Pepperoni'], excludedTools: ['Knife'], minNumberOfToppings: 2, maxNumberOfToppings: 6 });
  sleep(1);
  const denied = http.post(`${baseUrl}/api/pizza`, '{}', {
    headers: { 'Content-Type': 'application/json' }, tags: { operation: 'unauthorized' },
    timeout: '10s', responseCallback: http.expectedStatuses(401),
  });
  const body = json(denied);
  check(denied, {
    'unauthorized: HTTP 401': r => r.status === 401,
    'unauthorized: error without pizza': () => body?.error === 'authentication failed' && !Object.hasOwn(body, 'pizza'),
  });
  sleep(1);
}

export function handleSummary(data) {
  return { 'results/k6-summary.json': JSON.stringify(data, null, 2) };
}
