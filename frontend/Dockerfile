# Frontend Dockerfile - Production Ready
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage with Nginx
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

+++ frontend/Dockerfile (修改后)
     1	# Frontend Dockerfile - Production Ready
     2	FROM node:18-alpine AS builder
     3	
     4	WORKDIR /app
     5	
     6	# Copy package files
     7	COPY package*.json ./
     8	
     9	# Install dependencies - use npm ci if package-lock.json exists, otherwise npm install
    10	RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
    11	
    12	# Copy source code
    13	COPY . .
    14	
    15	# Build the application
    16	RUN npm run build
    17	
    18	# Production stage with Nginx
    19	FROM nginx:alpine
    20	
    21	# Copy built assets from builder
    22	COPY --from=builder /app/dist /usr/share/nginx/html
    23	
    24	# Copy nginx configuration
    25	COPY nginx.conf /etc/nginx/conf.d/default.conf
    26	
    27	# Expose port 80
    28	EXPOSE 80
    29	
    30	# Health check
    31	HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    32	    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1
    33	
    34	# Start nginx
    35	CMD ["nginx", "-g", "daemon off;"]
    36	
