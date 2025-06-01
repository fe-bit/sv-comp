import time
from tqdm import tqdm

def delete_entries_in_collection(collection, ids=None, batch_size=100):
    """
    Deletes entries in the specified collection by their IDs.
    If ids is None, deletes all entries in the collection.
    
    Args:
        collection: The collection from which to delete entries.
        ids: List of IDs to delete. If None, deletes all entries.
        batch_size: Number of entries to delete in a single batch.
    """
    if ids is None:
        # Delete all entries in the collection in batches
        try:
            count = collection.count()
            if count == 0:
                print("Collection is already empty.")
                return 0
            
            deleted_count = 0
            
            # Process in batches to avoid memory issues
            for i in tqdm(range(0, count, batch_size), desc="Delete Entries from Collection"):
                batch_ids = collection.get(limit=batch_size, offset=0)["ids"]
                if not batch_ids:
                    break
                    
                collection.delete(ids=batch_ids)
                deleted_count += len(batch_ids)
                time.sleep(0.1)  # Small delay to avoid overloading
                
            return deleted_count
        except Exception as e:
            print(f"Error deleting all entries: {str(e)}")
            return 0
    else:
        # Delete specific entries by ID
        try:
            collection.delete(ids=ids)
            print(f"Successfully deleted {len(ids)} entries from the collection.")
            return len(ids)
        except Exception as e:
            print(f"Error deleting entries: {str(e)}")
            return 0


def transfer_entries(source_collection, target_collection, ids, batch_size=100):
    """
    Transfers entries with specified IDs from source collection to target collection.
    
    Args:
        source_collection: The source collection to transfer from.
        target_collection: The target collection to transfer to.
        ids: List of IDs to transfer.
        batch_size: Number of entries to process in a single batch.
    """
    if not ids:
        print("No IDs provided for transfer.")
        return
    else:
        ids = [str(id) for id in ids]  # Ensure IDs are strings
    
    # Process in batches to avoid memory issues
    total_transferred = 0
    
    # Process IDs in batches
    for i in tqdm(range(0, len(ids), batch_size), desc="Insert Entries into Collection"):
        batch_ids = ids[i:i+batch_size]
        
        # Get the specific entries from source collection
        source_entries = source_collection.get(
            ids=batch_ids,
            include=["embeddings", "documents", "metadatas"]
        )
        
        # Skip if no entries found
        if len(source_entries["ids"]) == 0:
            continue
        
        # Check if we got all the data we need
        if "embeddings" not in source_entries or source_entries["embeddings"] is None:
            print(f"Warning: Missing embeddings data in batch {i}")
            continue
            
        # Check for IDs that already exist in target collection
        existing_ids = target_collection.get(
            ids=source_entries["ids"],
            include=[]
        )["ids"]
        
        # Filter out existing IDs
        new_indices = [idx for idx, id in enumerate(source_entries["ids"]) if id not in existing_ids]
        
        if not new_indices:
            continue  # Skip if all IDs already exist
            
        # Add only new entries to target collection
        try:
            # Extract data for new indices
            new_ids = [source_entries["ids"][idx] for idx in new_indices]
            new_embeddings = [source_entries["embeddings"][idx] for idx in new_indices]
            new_documents = [source_entries["documents"][idx] for idx in new_indices]
            new_metadatas = [source_entries["metadatas"][idx] for idx in new_indices]
            
            # Add to target collection
            target_collection.add(
                ids=new_ids,
                embeddings=new_embeddings,
                documents=new_documents,
                metadatas=new_metadatas
            )
            
            total_transferred += len(new_ids)
            
        except ValueError as e:
            print(f"Error during batch starting at {i}: {str(e)}")
            print("Trying alternative approach for this batch...")
            
            # Alternative approach: add one by one
            for idx in new_indices:
                try:
                    target_collection.add(
                        ids=[source_entries["ids"][idx]],
                        embeddings=[source_entries["embeddings"][idx]],
                        documents=[source_entries["documents"][idx]],
                        metadatas=[source_entries["metadatas"][idx]]
                    )
                    total_transferred += 1
                except Exception as inner_e:
                    print(f"Failed to add entry {source_entries['ids'][idx]}: {str(inner_e)}")
    