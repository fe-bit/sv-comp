from django.core.management.base import BaseCommand
from .strategy.category_virtual_verifier import evaluate_category_best_verifier
from .strategy.best_virtual_verifier import evaluate_virtually_best_verifier
from .strategy.knn_1_embed import evaluate_knn_1_best_verifier
from .strategy.knn_5_majority_vote import evaluate_knn_5_majority_vote_best_verifier
from .strategy.knn_5_distance_vote import evaluate_knn_5_distance_weighted
from .strategy.data import get_train_test_data
import pandas as pd
from benchmarks.models import Benchmark
from verification_tasks.embedding.embedder import embed_verifications_tasks
from verification_tasks.embedding.config import get_collection, get_test_collection, get_train_collection
from verification_tasks.models import VerificationTask, VerificationCategory
from tqdm import tqdm
import time

class Command(BaseCommand):
    help = "Manages embedding collections - transfers entries and cleans collections"

    def handle(self, *args, **options):
        # Get all collections
        main_collection = get_collection()
        test_collection = get_test_collection()
        train_collection = get_train_collection()

        # Show initial collection sizes
        print("Initial collection sizes:")
        print(f"Main collection: {main_collection.count()}")
        print(f"Test collection: {test_collection.count()}")
        print(f"Train collection: {train_collection.count()}")

        # Transfer all entries from test collection to main collection
        print("Transferring entries from test collection to main collection...")
        
        # Get all entries from test collection
        batch_size = 100  # Process in batches to avoid memory issues
        test_count = test_collection.count()
        
        for i in tqdm(range(0, test_count, batch_size), desc="Transferring entries"):
            # Get a batch of entries from test collection with include to ensure we get all data
            test_entries = test_collection.get(
                limit=batch_size, 
                offset=i,
                include=["embeddings", "documents", "metadatas"]
            )
            
            # Skip if no entries found
            if len(test_entries["ids"]) == 0:
                continue
            
            # Check if we got all the data we need
            if "embeddings" not in test_entries or test_entries["embeddings"] is None:
                print(f"Warning: Missing embeddings data in batch {i}")
                continue
                
            # Check for IDs that already exist in main collection
            existing_ids = main_collection.get(
                ids=test_entries["ids"],
                include=[]
            )["ids"]
            
            # Filter out existing IDs
            new_indices = [idx for idx, id in enumerate(test_entries["ids"]) if id not in existing_ids]
            
            if not new_indices:
                continue  # Skip if all IDs already exist
                
            # Add only new entries to main collection
            try:
                # Extract data for new indices
                new_ids = [test_entries["ids"][idx] for idx in new_indices]
                new_embeddings = [test_entries["embeddings"][idx] for idx in new_indices]
                new_documents = [test_entries["documents"][idx] for idx in new_indices]
                new_metadatas = [test_entries["metadatas"][idx] for idx in new_indices]
                
                # Add to main collection
                main_collection.add(
                    ids=new_ids,
                    embeddings=new_embeddings,
                    documents=new_documents,
                    metadatas=new_metadatas
                )
                # Add small delay to avoid overloading
                time.sleep(0.1)
            except ValueError as e:
                print(f"Error during batch starting at {i}: {str(e)}")
                print("Trying alternative approach for this batch...")
                
                # Alternative approach: add one by one
                for idx in new_indices:
                    try:
                        main_collection.add(
                            ids=[test_entries["ids"][idx]],
                            embeddings=[test_entries["embeddings"][idx]],
                            documents=[test_entries["documents"][idx]],
                            metadatas=[test_entries["metadatas"][idx]]
                        )
                    except Exception as inner_e:
                        print(f"Failed to add entry {test_entries['ids'][idx]}: {str(inner_e)}")
        
        # Clear test and train collections (uncomment when transfer is successful)
        print("Clearing test and train collections...")
        
        # Safe deletion with batching
        def safe_delete_collection(collection, name):
            try:
                count = collection.count()
                if count > 0:
                    print(f"Deleting {count} entries from {name} collection...")
                    for i in tqdm(range(0, count, batch_size), desc=f"Deleting from {name}"):
                        ids_to_delete = collection.get(limit=batch_size, offset=i)["ids"]
                        if ids_to_delete:
                            collection.delete(ids_to_delete)
                            time.sleep(0.1)  # Small delay to avoid overloading
            except Exception as e:
                print(f"Error clearing {name} collection: {str(e)}")
        
        safe_delete_collection(test_collection, "test")
        safe_delete_collection(train_collection, "train")
        
        # Show final collection sizes
        print("\nFinal collection sizes:")
        print(f"Main collection: {main_collection.count()}")
        print(f"Test collection: {test_collection.count()}")
        print(f"Train collection: {train_collection.count()}")
        
        print("\nTransfer and cleanup completed successfully.")

